import spacy
import yaml
import csv
import argparse
from typing import Dict, Any, List
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern, EntityRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer import RecognizerResult
from presidio_anonymizer import AnonymizerEngine, operators
from presidio_anonymizer.entities import OperatorConfig
import warnings
warnings.filterwarnings("ignore", message=".*resume_download.*", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*You are using `torch.load` with `weights_only=False`.*", category=FutureWarning)




def initialize_anonymizer(engine_name: str, lang_code: str, model_name: str) -> 'Anonymizer':
    """
    Initialize an anonymizer object based on configuration settings.

    Args:
        engine_name (str): Name of the NLP engine.
        lang_code (str): Language code for the NLP model.
        model_name (str): Name of the NLP model.

    Returns:
        Anonymizer: An initialized Anonymizer object.
    """
    nlp_model = spacy.load(model_name)
    configuration = {
        "nlp_engine_name": engine_name,
        "models": [{"lang_code": lang_code, "model_name": model_name}]
    }
    return Anonymizer(nlp_model, configuration)

class CSVAnonymizerUtility:
    """
    Utility class for anonymizing CSV files.

    Attributes:
        anonymizer (Anonymizer): An instance of the Anonymizer to use for processing rows.
    """
    def __init__(self, anonymizer: 'Anonymizer'):
        self.anonymizer = anonymizer

    def anonymize_csv(self, input_file_path: str, output_file_path: str) -> None:
        """
        Read a CSV file, anonymize its contents, and write the results to another CSV file.

        Args:
            input_file_path (str): Path to the input CSV file.
            output_file_path (str): Path to the output CSV file where anonymized data will be stored.
        """
        try:
            with open(input_file_path, newline='', encoding='utf-8') as csvfile, \
                    open(output_file_path, 'w', newline='', encoding='utf-8') as outputfile:
                reader = csv.reader(csvfile)
                writer = csv.writer(outputfile)
                for i, row in enumerate(reader):
                    if i % 10 == 0:
                        print(f"{i}行目を処理中...")
                    anonymized_row = self.anonymizer.process_row(row)
                    writer.writerow(anonymized_row)
        except FileNotFoundError:
            print("File not found:", input_file_path)
        except IOError as e:
            print("Error handling file:", e)

class Anonymizer:
    """
    テキストの匿名化を行うクラス。

    Attributes:
        nlp (spacy.Language): spaCy NLPモデルインスタンス。
        configuration (dict): Presidio NLPエンジン設定。
    """
    def __init__(self, nlp: spacy.Language, configuration: dict):
        self.analyzer = self.setup_analyzer(nlp, configuration)
        self.anonymizer_engine = AnonymizerEngine()

    def setup_analyzer(self, nlp: spacy.Language, configuration: dict) -> AnalyzerEngine:
        """
        Analyzerエンジンを設定し、Recognizerをレジストリに登録します。

        Args:
            nlp (spacy.Language): 使用するNLPモデル。
            configuration (dict): NLPエンジンの設定。

        Returns:
            AnalyzerEngine: 設定済みのAnalyzerEngineオブジェクト。
        """
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()
        registry = RecognizerRegistry()
        registry.add_recognizer(SpacyJapaneseNameRecognizer(nlp))
        registry.add_recognizer(
            PatternRecognizer(
                supported_entity="USER_ID",
                patterns=[Pattern('user_id', r'[A-Za-z]\d{7}', 0.95)],
                supported_language="ja"
            )
        )
        # Registryが日本語をサポートするように設定
        registry.supported_languages = ["ja"]
        return AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["ja"], registry=registry)

    def process_row(self, row: List[str]) -> List[str]:
        """
        与えられたCSVの行を受け取り、各セルを解析して匿名化し、結果をリストとして返します。

        Args:
            row (List[str]): CSVから読み込まれた一行分のデータ。

        Returns:
            List[str]: 匿名化された行データ。
        """
        anonymized_row = []
        for cell in row:
            if cell.strip():  # Ignore empty cells
                analyzer_result = self.analyzer.analyze(text=cell, language="ja")
                anonymized_cell = self.anonymizer_engine.anonymize(
                    text=cell,
                    analyzer_results=analyzer_result,
                    operators={
                        "USER_ID": OperatorConfig("replace", {"new_value": "<USER_ID>"}),
                        "PERSON": OperatorConfig("replace", {"new_value": "<PERSON>"})
                    }
                )
                anonymized_row.append(anonymized_cell.text)
            else:
                anonymized_row.append(cell)
        return anonymized_row

class SpacyJapaneseNameRecognizer(EntityRecognizer):
    """
    spaCyを使用して日本語の人名を検出するEntityRecognizerのカスタム実装。
    """
    def __init__(self, nlp: spacy.Language, supported_language: str = "ja"):
        super().__init__(supported_entities=["PERSON"], supported_language=supported_language)
        self.nlp = nlp
        self.supported_language = supported_language

    def analyze(self, text: str, entities: list, nlp_artifacts=None) -> List[RecognizerResult]:
        """
        与えられたテキスト内の人名を検出し、結果をリストで返します。

        Args:
            text (str): 解析するテキスト。
            entities (list): 検出対象のエンティティタイプ。

        Returns:
            List[RecognizerResult]: 検出されたエンティティのリスト。
        """
        results = []
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == "Person":
                results.append(RecognizerResult(
                    entity_type="PERSON",
                    start=ent.start_char,
                    end=ent.end_char,
                    score=1.0
                ))
        return results

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Anonymize CSV files using specified settings.")
    parser.add_argument('--engine_name', type=str, default='spacy', help='Name of the NLP engine to use.')
    parser.add_argument('--lang_code', type=str, default='ja', help='Language code for the NLP model.')
    parser.add_argument('--model_name', type=str, default='ja_ginza_electra', help='Name of the NLP model to use.')
    parser.add_argument('--input', type=str, default='data.csv', help='Path to the input CSV file.')
    parser.add_argument('--output', type=str, default='result.csv', help='Path to the output CSV file.')
    return parser.parse_args()

def main():
    args = parse_arguments()

    anonymizer = initialize_anonymizer(args.engine_name, args.lang_code, args.model_name)
    utility = CSVAnonymizerUtility(anonymizer)
    utility.anonymize_csv(args.input, args.output)

if __name__ == "__main__":
    main()
