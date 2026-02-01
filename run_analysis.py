#!/usr/bin/env python3
"""
Command-line tool for running stock analysis without Telegram
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

from config import settings
from crews.research_crew import analyze_stock_sync


console = Console()


def run_analysis(symbol: str, analysis_type: str = "full"):
    """Run stock analysis and display results."""
    
    console.print(Panel.fit(
        f"[bold blue]Stock Research Assistant[/bold blue]\n"
        f"Analyzing: [bold green]{symbol}[/bold green]\n"
        f"Type: {analysis_type}",
        title="🔬 AI Research",
    ))
    
    if not settings.mistral_api_key:
        console.print("[red]❌ Error: MISTRAL_API_KEY not set![/red]")
        console.print("\nPlease add your Mistral API key to the .env file:")
        console.print("MISTRAL_API_KEY=your_key_here")
        return
    
    console.print(f"\n⏳ Starting {analysis_type} analysis for [bold]{symbol}[/bold]...")
    console.print("This may take 2-3 minutes for full analysis.\n")
    
    start_time = datetime.now()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("AI agents working...", total=None)
        
        try:
            report = analyze_stock_sync(symbol, analysis_type)
            progress.update(task, description="✅ Analysis complete!")
        except Exception as e:
            progress.update(task, description=f"❌ Error: {str(e)[:50]}")
            console.print(f"\n[red]Error during analysis:[/red] {e}")
            return
    
    elapsed = (datetime.now() - start_time).seconds
    
    console.print(f"\n⏱️  Completed in {elapsed} seconds\n")
    console.print("=" * 60)
    
    # Display the report
    try:
        md = Markdown(report)
        console.print(md)
    except:
        # Fallback to plain text if markdown fails
        console.print(report)
    
    console.print("\n" + "=" * 60)
    console.print("[dim]⚠️ Disclaimer: For educational purposes only. Not financial advice.[/dim]")


def quick_check(symbol: str):
    """Quick price check without AI analysis."""
    import json
    from tools.market_data import get_stock_price, get_stock_info
    
    console.print(f"\n⚡ Quick check for [bold]{symbol}[/bold]...\n")
    
    try:
        price_data = json.loads(get_stock_price.run(symbol))
        info_data = json.loads(get_stock_info.run(symbol))
        
        if "error" in price_data:
            console.print(f"[red]❌ Error: {price_data['error']}[/red]")
            return
        
        change = price_data.get("change", 0)
        trend = "🟢" if change >= 0 else "🔴"
        
        console.print(Panel.fit(
            f"{trend} [bold]{symbol}[/bold] - {info_data.get('company_name', 'N/A')}\n\n"
            f"💰 Price: ₹{price_data.get('current_price', 0):,.2f}\n"
            f"📊 Change: ₹{change:+,.2f} ({price_data.get('change_percent', 0):+.2f}%)\n\n"
            f"📈 High: ₹{price_data.get('high', 0):,.2f}\n"
            f"📉 Low: ₹{price_data.get('low', 0):,.2f}\n"
            f"📊 Volume: {price_data.get('volume', 0):,}\n\n"
            f"🏢 Sector: {info_data.get('sector', 'N/A')}\n"
            f"📊 Market Cap: {info_data.get('market_cap_category', 'N/A')}",
            title="Quick Overview",
        ))
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")


def list_stocks():
    """List popular stocks."""
    from config import NIFTY50_STOCKS, SECTORS
    
    console.print("\n[bold]📊 NIFTY 50 Stocks:[/bold]\n")
    
    for i in range(0, len(NIFTY50_STOCKS), 10):
        row = NIFTY50_STOCKS[i:i+10]
        console.print("  " + " | ".join(f"[cyan]{s}[/cyan]" for s in row))
    
    console.print("\n[bold]🏭 Sectors:[/bold]\n")
    for sector, stocks in SECTORS.items():
        console.print(f"  [yellow]{sector}:[/yellow] {', '.join(stocks[:5])}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Stock Research Assistant for Indian Markets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_analysis.py RELIANCE          # Full analysis
  python run_analysis.py TCS --quick       # Quick price check
  python run_analysis.py INFY --type quick # Quick AI analysis
  python run_analysis.py --list            # List stocks
        """,
    )
    
    parser.add_argument(
        "symbol",
        nargs="?",
        help="Stock symbol (e.g., RELIANCE, TCS, INFY)",
    )
    
    parser.add_argument(
        "--type",
        choices=["full", "quick", "technical-only"],
        default="full",
        help="Type of analysis (default: full)",
    )
    
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Quick price check without AI analysis",
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List popular stocks",
    )
    
    args = parser.parse_args()
    
    console.print("\n[bold blue]🇮🇳 Stock Research Assistant[/bold blue]")
    console.print("[dim]AI-Powered Analysis for Indian Markets[/dim]\n")
    
    if args.list:
        list_stocks()
        return
    
    if not args.symbol:
        parser.print_help()
        console.print("\n[yellow]💡 Tip: Try 'python run_analysis.py RELIANCE'[/yellow]\n")
        return
    
    symbol = args.symbol.upper().strip()
    
    if args.quick:
        quick_check(symbol)
    else:
        run_analysis(symbol, args.type)


if __name__ == "__main__":
    main()
