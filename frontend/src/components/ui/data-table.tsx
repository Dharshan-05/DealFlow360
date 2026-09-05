"use client";

import React, { useState } from "react";
import { ArrowUpDown, ArrowUp, ArrowDown, ChevronLeft, ChevronRight } from "lucide-react";
import { LoadingState } from "@/components/ui/loading-state";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface ColumnDef<TData> {
  id: string;
  header: string | React.ReactNode;
  accessorKey?: keyof TData;
  cell?: (row: TData) => React.ReactNode;
  sortable?: boolean;
  align?: "left" | "center" | "right";
  className?: string;
}

export interface DataTableProps<TData> {
  columns: ColumnDef<TData>[];
  data: TData[];
  keyExtractor: (item: TData) => string;
  isLoading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyAction?: React.ReactNode;
  pageSize?: number;
  selectable?: boolean;
  selectedIds?: string[];
  onSelectionChange?: (selectedIds: string[]) => void;
  className?: string;
  compact?: boolean;
}

export function DataTable<TData>({
  columns,
  data,
  keyExtractor,
  isLoading = false,
  error = null,
  onRetry,
  emptyTitle = "No records found",
  emptyDescription = "There are currently no items matching your criteria.",
  emptyAction,
  pageSize = 10,
  selectable = false,
  selectedIds = [],
  onSelectionChange,
  className,
  compact = false,
}: DataTableProps<TData>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [currentPage, setCurrentPage] = useState<number>(1);

  // Sorting
  const sortedData = React.useMemo(() => {
    if (!sortKey) return data;

    const column = columns.find((c) => c.id === sortKey);
    if (!column || !column.accessorKey) return data;

    return [...data].sort((a, b) => {
      const aVal = a[column.accessorKey!];
      const bVal = b[column.accessorKey!];

      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      const comparison = aVal > bVal ? 1 : -1;
      return sortOrder === "asc" ? comparison : -comparison;
    });
  }, [data, sortKey, sortOrder, columns]);

  // Pagination
  const totalPages = Math.ceil(sortedData.length / pageSize) || 1;
  const paginatedData = React.useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, currentPage, pageSize]);

  const handleSort = (colId: string) => {
    if (sortKey === colId) {
      if (sortOrder === "asc") {
        setSortOrder("desc");
      } else {
        setSortKey(null);
        setSortOrder("asc");
      }
    } else {
      setSortKey(colId);
      setSortOrder("asc");
    }
  };

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!onSelectionChange) return;
    if (e.target.checked) {
      const allIds = data.map(keyExtractor);
      onSelectionChange(allIds);
    } else {
      onSelectionChange([]);
    }
  };

  const handleSelectRow = (id: string) => {
    if (!onSelectionChange) return;
    if (selectedIds.includes(id)) {
      onSelectionChange(selectedIds.filter((item) => item !== id));
    } else {
      onSelectionChange([...selectedIds, id]);
    }
  };

  if (error) {
    return (
      <div className="rounded-xl border border-border bg-card p-4">
        <ErrorState
          variant="server"
          title="Failed to Load Data"
          message={error}
          onRetry={onRetry}
        />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="rounded-xl border border-border bg-card p-6">
        <LoadingState message="Retrieving data records..." variant="spinner" />
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-4">
        <EmptyState
          title={emptyTitle}
          description={emptyDescription}
          action={emptyAction}
        />
      </div>
    );
  }

  const allSelected = data.length > 0 && selectedIds.length === data.length;
  const someSelected = selectedIds.length > 0 && selectedIds.length < data.length;

  return (
    <div className={cn("space-y-4", className)}>
      <div className="overflow-x-auto rounded-xl border border-border bg-card shadow-sm">
        <table className="w-full text-left border-collapse text-sm">
          <thead className="border-b border-border bg-slate-50 text-slate-600 font-semibold uppercase text-xs tracking-wider">
            <tr>
              {selectable && (
                <th scope="col" className="p-4 w-10">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    ref={(el) => {
                      if (el) el.indeterminate = someSelected;
                    }}
                    onChange={handleSelectAll}
                    aria-label="Select all rows"
                    className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                  />
                </th>
              )}
              {columns.map((column) => {
                const isSorted = sortKey === column.id;
                const alignClass =
                  column.align === "right"
                    ? "text-right"
                    : column.align === "center"
                    ? "text-center"
                    : "text-left";

                return (
                  <th
                    key={column.id}
                    scope="col"
                    className={cn(
                      compact ? "px-3 py-2.5" : "px-4 py-3.5",
                      alignClass,
                      column.className
                    )}
                  >
                    {column.sortable ? (
                      <button
                        type="button"
                        onClick={() => handleSort(column.id)}
                        className="inline-flex items-center gap-1.5 font-semibold text-slate-700 hover:text-foreground focus:outline-none"
                      >
                        <span>{column.header}</span>
                        {isSorted ? (
                          sortOrder === "asc" ? (
                            <ArrowUp className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                          ) : (
                            <ArrowDown className="h-3.5 w-3.5 text-primary" aria-hidden="true" />
                          )
                        ) : (
                          <ArrowUpDown className="h-3.5 w-3.5 text-slate-400 opacity-60" aria-hidden="true" />
                        )}
                      </button>
                    ) : (
                      column.header
                    )}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-border text-foreground">
            {paginatedData.map((row) => {
              const rowId = keyExtractor(row);
              const isSelected = selectedIds.includes(rowId);

              return (
                <tr
                  key={rowId}
                  className={cn(
                    "transition-colors hover:bg-slate-50/70",
                    isSelected && "bg-blue-50/40"
                  )}
                >
                  {selectable && (
                    <td className="p-4 w-10">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleSelectRow(rowId)}
                        aria-label={`Select row ${rowId}`}
                        className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                      />
                    </td>
                  )}
                  {columns.map((column) => {
                    const alignClass =
                      column.align === "right"
                        ? "text-right"
                        : column.align === "center"
                        ? "text-center"
                        : "text-left";

                    return (
                      <td
                        key={column.id}
                        className={cn(
                          compact ? "px-3 py-2 text-xs" : "px-4 py-3 text-sm",
                          alignClass,
                          column.className
                        )}
                      >
                        {column.cell
                          ? column.cell(row)
                          : column.accessorKey
                          ? String(row[column.accessorKey] ?? "")
                          : null}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-2 text-xs text-muted">
          <span>
            Showing {(currentPage - 1) * pageSize + 1} to{" "}
            {Math.min(currentPage * pageSize, sortedData.length)} of {sortedData.length} records
          </span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              aria-label="Previous page"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline ml-1">Previous</span>
            </Button>
            <span className="px-2 font-medium">
              Page {currentPage} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              aria-label="Next page"
            >
              <span className="hidden sm:inline mr-1">Next</span>
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
