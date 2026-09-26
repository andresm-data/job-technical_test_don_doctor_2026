"""CLI interna del pipeline."""
import argparse
from datetime import datetime
from pathlib import Path

from .config import build_config
from .runner import run_pipeline


# =============================================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]


# =============================================================================
def build_parser() -> argparse.ArgumentParser:
    """Crea el parser principal.

    Returns:
        argparse.ArgumentParser: Parser configurado.
    """

    parser = argparse.ArgumentParser(
        description='Ejecuta el pipeline piloto de DonDoctor.'
    )

    parser.add_argument(
        'run',
        nargs='?',
        default='run',
        help='Comando único del pipeline. Se mantiene como texto para que la CLI sea estable.',
    )
    parser.add_argument(
        '--landing-dir',
        type=Path,
        default=None,
        help='Ruta de la carpeta con los archivos fuente.',
    )
    parser.add_argument(
        '--warehouse-path',
        type=Path,
        default=None,
        help='Ruta del archivo DuckDB a generar.',
    )
    parser.add_argument(
        '--cutoff-at',
        type=datetime.fromisoformat,
        default=None,
        help='Fecha de corte para revisar citas futuras con estado cerrado.',
    )

    return parser


# =============================================================================
def main() -> int:
    """Ejecuta la CLI del pipeline.

    Returns:
        int: Código de salida del proceso.
    """
    parser = build_parser()
    args = parser.parse_args()

    if args.run != 'run':
        parser.error("El único comando disponible es 'run'.")

    config = build_config(
        root_dir=PROJECT_ROOT,
        landing_dir=args.landing_dir,
        warehouse_path=args.warehouse_path,
        cutoff_at=args.cutoff_at
    )

    run_pipeline(config)

    return 0
