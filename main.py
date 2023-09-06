#!/bin/env python
"""The main entry point for the bot."""
import typer

from scraper.telegram import init_telegram

cli = typer.Typer()


@cli.command()
def run():
    """Actually start the bot."""
    app = init_telegram()
    typer.echo("Starting the bot in polling mode.")
    app.run_polling()


if __name__ == "__main__":
    cli()
