import csv
import io
import json
from typing import Any, Dict, List
from fastapi.responses import StreamingResponse


class ReportExporter:
    """
    Streaming multi-format exporter for domain reports (Phase 369).
    Strict RFC-4180 CSV escaping, UTF-8 encoded with safe Content-Disposition headers.
    """

    @staticmethod
    def export_to_csv(
        filename: str,
        columns: List[str],
        rows: List[Dict[str, Any]],
    ) -> StreamingResponse:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        for r in rows:
            formatted_row = {
                k: (str(r.get(k, "")) if r.get(k) is not None else "")
                for k in columns
            }
            writer.writerow(formatted_row)

        output.seek(0)
        sanitized_filename = filename.replace(" ", "_").replace("/", "_")
        if not sanitized_filename.endswith(".csv"):
            sanitized_filename += ".csv"

        response = StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv; charset=utf-8",
        )
        response.headers["Content-Disposition"] = f'attachment; filename="{sanitized_filename}"'
        return response

    @staticmethod
    def export_to_json(
        filename: str,
        data: Any,
    ) -> StreamingResponse:
        sanitized_filename = filename.replace(" ", "_").replace("/", "_")
        if not sanitized_filename.endswith(".json"):
            sanitized_filename += ".json"

        content = json.dumps(data, default=str, indent=2)
        response = StreamingResponse(
            iter([content]),
            media_type="application/json; charset=utf-8",
        )
        response.headers["Content-Disposition"] = f'attachment; filename="{sanitized_filename}"'
        return response
