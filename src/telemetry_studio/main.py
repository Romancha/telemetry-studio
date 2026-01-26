"""Entry point for Telemetry Studio server."""

import argparse


def main():
    """Start the Telemetry Studio server."""
    parser = argparse.ArgumentParser(
        description="Telemetry Studio - Web interface for telemetry video overlay configuration"
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Host to bind to (default: from config or 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind to (default: from config or 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    args = parser.parse_args()

    # Import here to avoid circular imports and allow config override
    from telemetry_studio.config import settings

    host = args.host or settings.host
    port = args.port or settings.port

    import uvicorn

    print(f"Starting Telemetry Studio at http://{host}:{port}")
    print("Press Ctrl+C to stop")

    uvicorn.run(
        "telemetry_studio.app:app",
        host=host,
        port=port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
