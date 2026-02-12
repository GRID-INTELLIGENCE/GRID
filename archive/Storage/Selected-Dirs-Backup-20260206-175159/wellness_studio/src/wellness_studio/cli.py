"""
Wellness Studio - Command Line Interface
Simple, intuitive CLI for the wellness transformation pipeline.
"""
import argparse
import sys
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .pipeline import WellnessPipeline, run_pipeline
from .config import path_config, model_config, processing_config


def create_console():
    """Create rich console if available, else use print."""
    if RICH_AVAILABLE:
        return Console()
    return None


def print_banner(console=None):
    """Print welcome banner."""
    banner = """
    🌿 WELLNESS STUDIO 🌿

    Transform Your Health Journey
    Where Modern Medicine Meets Natural Wellness
    """

    if console:
        console.print(Panel.fit(
            Text(banner, style="green"),
            title="Welcome",
            border_style="green"
        ))
    else:
        print(banner)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Wellness Studio - Transform medical data into natural wellness plans',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a prescription PDF
  python -m wellness_studio.cli prescription.pdf --patient "John Doe"

  # Process raw text
  python -m wellness_studio.cli -t "Patient takes Xanax for anxiety, wants natural alternatives"

  # Process with specific device
  python -m wellness_studio.cli report.pdf --device cpu --format html
        """
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        'file',
        nargs='?',
        help='Path to input file (PDF, TXT, DOCX, or audio)'
    )
    input_group.add_argument(
        '-t', '--text',
        help='Raw text input (alternative to file)'
    )

    # Processing options
    parser.add_argument(
        '--patient', '-p',
        help='Patient name or identifier'
    )
    parser.add_argument(
        '--case-type', '-c',
        default='general',
        choices=['general', 'prescription', 'symptom', 'report'],
        help='Type of medical case (default: general)'
    )
    parser.add_argument(
        '--device', '-d',
        default='auto',
        choices=['auto', 'cpu', 'cuda', 'mps'],
        help='Compute device (default: auto)'
    )
    parser.add_argument(
        '--format', '-f',
        default='markdown',
        choices=['markdown', 'html', 'json'],
        help='Output format (default: markdown)'
    )
    parser.add_argument(
        '--save-embeddings', '-e',
        action='store_true',
        help='Save embeddings to file'
    )
    parser.add_argument(
        '--skip-embeddings',
        action='store_true',
        help='Skip embedding generation (faster)'
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=Path,
        help='Custom output directory for reports'
    )

    # Info options
    parser.add_argument(
        '--models',
        action='store_true',
        help='Show model information and exit'
    )
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='Wellness Studio 1.0.0'
    )

    args = parser.parse_args()

    console = create_console()

    # Show model info
    if args.models:
        print_model_info(console)
        return 0

    # Print banner
    print_banner(console)

    # Validate input
    if args.file and not Path(args.file).exists():
        print(f"Error: File not found: {args.file}")
        return 1

    # Run pipeline
    try:
        pipeline = WellnessPipeline(
            device=args.device,
            skip_embeddings=args.skip_embeddings
        )

        if console:
            console.print(f"\n[bold green]Processing your wellness case...[/bold green]\n")
        else:
            print("Processing your wellness case...\n")

        result = pipeline.process(
            input_path=args.file,
            text_input=args.text,
            patient_name=args.patient,
            case_type=args.case_type,
            output_format=args.format,
            save_embeddings=args.save_embeddings
        )

        if result.success:
            if console:
                console.print(Panel.fit(
                    f"[bold green]✅ Success![/bold green]\n\n"
                    f"Report saved to: [cyan]{result.report_path}[/cyan]\n"
                    f"Processing time: [yellow]{result.processing_time:.2f}s[/yellow]",
                    title="Complete",
                    border_style="green"
                ))
            else:
                print(f"\n✅ Success!")
                print(f"Report saved to: {result.report_path}")
                print(f"Processing time: {result.processing_time:.2f}s")

            return 0
        else:
            if console:
                console.print(Panel.fit(
                    f"[bold red]❌ Error:[/bold red] {result.error_message}",
                    title="Failed",
                    border_style="red"
                ))
            else:
                print(f"\n❌ Error: {result.error_message}")

            return 1

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        return 130
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


def print_model_info(console=None):
    """Display information about configured models."""
    info = f"""
[bold]Configured Models:[/bold]

📝 [bold]Medical Scribe (Llama 3.1):[/bold]
   Model: {model_config.SCRIBE_MODEL}
   Purpose: Structure unstructured medical data

🔢 [bold]Embedding Model:[/bold]
   Model: {model_config.EMBEDDING_MODEL}
   Purpose: Create vector representations of medical cases

🏥 [bold]Medical Document Model (HuatuoGPT):[/bold]
   Model: {model_config.MEDICAL_MODEL}
   Purpose: Generate natural wellness alternatives

[bold]Processing Configuration:[/bold]
Device: {model_config.DEVICE}
Chunk Size: {processing_config.CHUNK_SIZE}
Output Directory: {path_config.REPORTS_DIR}
"""

    if console:
        console.print(Panel(info, title="Model Information", border_style="blue"))
    else:
        print(info)


def quick_cli():
    """Quick interactive CLI for simple use."""
    console = create_console()
    print_banner(console)

    print("\nQuick Mode - Enter your case details:")
    print("(Describe symptoms, medications, or upload a file path)")
    print("Type 'quit' to exit\n")

    pipeline = WellnessPipeline()

    while True:
        try:
            user_input = input("wellness> ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 🌿")
                break

            if not user_input:
                continue

            # Check if input is a file path
            if Path(user_input).exists():
                result = pipeline.process(input_path=user_input)
            else:
                result = pipeline.quick_process(text=user_input)

            if result.success:
                print(f"✅ Report generated: {result.report_path}")
            else:
                print(f"❌ Error: {result.error_message}")

        except KeyboardInterrupt:
            print("\nGoodbye! 🌿")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == '__main__':
    sys.exit(main())
