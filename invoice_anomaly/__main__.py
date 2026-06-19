import argparse
from .pipeline import AnomalyPipeline
from .train_pipeline import TrainPipeline

def main():
    parser = argparse.ArgumentParser(description="Invoice Anomaly Detection System")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    detect_parser = subparsers.add_parser("detect", help="Run the anomaly detection pipeline")
    detect_parser.add_argument("--invoices", required=True, help="Path to the invoice headers CSV")
    detect_parser.add_argument("--lines", required=True, help="Path to the invoice lines CSV")
    detect_parser.add_argument("--output", required=True, help="Path to save the results CSV")

    train_parser = subparsers.add_parser("train", help="Run the model training pipeline")
    train_parser.add_argument("--invoices", required=True, help="Path to the training invoices CSV")
    train_parser.add_argument("--labels", required=True, help="Path to the labels CSV")

    args = parser.parse_args()

    if args.command == "detect":
        pipeline = AnomalyPipeline()
        pipeline.load_data(args.invoices, args.lines)
        pipeline.prepare_data()
        pipeline.build_invoices()
        pipeline.load_model()
        anomaly_types, anomaly_details = pipeline.detect_anomalies()
        pipeline.create_predictions(anomaly_types, anomaly_details, args.output)
        print(f"Detection complete. Results saved to: {args.output}")
        print(f"Additionally, file ({args.output.replace('.csv', '_with_details.csv')}) with detailed anomaly analysis has been generated in the same directory.")

    elif args.command == "train":
        pipeline = TrainPipeline()
        pipeline.load_train_data(args.invoices, args.labels)
        pipeline.prepare_train_data()
        pipeline.build_train_data()
        pipeline.train_model()
        print("Training complete. The model has been saved.")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()