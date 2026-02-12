"""Command-line interface for Coinbase."""

import click


@click.command()
@click.option(
    "--crypto",
    is_flag=True,
    help="Enable crypto scope",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
def main(crypto: bool, verbose: bool) -> None:
    """Coinbase CLI tool."""
    if crypto:
        click.echo("Crypto scope enabled")
    if verbose:
        click.echo("Verbose mode enabled")
    click.echo("Coinbase CLI running")


if __name__ == "__main__":
    main()
