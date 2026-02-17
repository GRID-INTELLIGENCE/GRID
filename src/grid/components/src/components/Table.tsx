import React, { useCallback, useMemo, useState } from "react";
import { useTheme } from "../hooks/useTheme";
import { BaseComponentProps, ComponentSize } from "../types";

export interface Column<T = any> {
  key: keyof T | string;
  title: string;
  width?: string | number;
  sortable?: boolean;
  filterable?: boolean;
  render?: (value: any, record: T, index: number) => React.ReactNode;
  filterRender?: (
    value: any,
    onChange: (value: any) => void
  ) => React.ReactNode;
}

export interface PaginationConfig {
  current: number;
  total: number;
  pageSize: number;
  showSizeChanger?: boolean;
  pageSizeOptions?: number[];
  onChange: (page: number, pageSize: number) => void;
  onShowSizeChange?: (current: number, size: number) => void;
}

export interface SortConfig {
  key: string;
  order: "asc" | "desc";
}

export interface FilterConfig {
  [key: string]: any;
}

export interface TableProps<T = any> extends BaseComponentProps {
  data: T[];
  columns: Column<T>[];
  loading?: boolean;
  pagination?: PaginationConfig | false;
  size?: ComponentSize;
  bordered?: boolean;
  striped?: boolean;
  hoverable?: boolean;
  scroll?: {
    x?: number | string;
    y?: number | string;
  };
  onSort?: (sortConfig: SortConfig | null) => void;
  onFilter?: (filters: FilterConfig) => void;
  rowKey?: keyof T | ((record: T) => string);
  expandable?: {
    expandedRowRender: (record: T, index: number) => React.ReactNode;
    rowExpandable?: (record: T) => boolean;
  };
  rowSelection?: {
    selectedRowKeys: string[];
    onChange: (selectedRowKeys: string[], selectedRows: T[]) => void;
    getCheckboxProps?: (record: T) => {
      disabled?: boolean;
      name?: string;
    };
  };
}

const sizeStyles: Record<ComponentSize, string> = {
  xs: "text-xs",
  sm: "text-sm",
  md: "text-base",
  lg: "text-lg",
  xl: "text-xl",
};

function Table<T = any>({
  data,
  columns,
  loading = false,
  pagination,
  size = "md",
  bordered = false,
  striped = false,
  hoverable = true,
  scroll,
  onSort,
  onFilter,
  rowKey = "id" as keyof T,
  expandable,
  rowSelection,
  className = "",
  style,
  "data-testid": testId,
}: TableProps<T>) {
  const theme = useTheme();
  const [sortConfig, setSortConfig] = useState<SortConfig | null>(null);
  const [filters, setFilters] = useState<FilterConfig>({});
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  // Get row key
  const getRowKey = useCallback(
    (record: T, index: number): string => {
      if (typeof rowKey === "function") {
        return rowKey(record);
      }
      return String(record[rowKey] ?? index);
    },
    [rowKey]
  );

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortConfig) return data;

    return [...data].sort((a, b) => {
      const aValue = a[sortConfig.key as keyof T];
      const bValue = b[sortConfig.key as keyof T];

      let result = 0;
      if (aValue < bValue) result = -1;
      if (aValue > bValue) result = 1;

      return sortConfig.order === "desc" ? -result : result;
    });
  }, [data, sortConfig]);

  // Filter data
  const filteredData = useMemo(() => {
    return sortedData.filter((record) => {
      return Object.entries(filters).every(([key, filterValue]) => {
        if (!filterValue) return true;
        const recordValue = record[key as keyof T];
        return String(recordValue)
          .toLowerCase()
          .includes(String(filterValue).toLowerCase());
      });
    });
  }, [sortedData, filters]);

  // Paginate data
  const paginatedData = useMemo(() => {
    if (!pagination) return filteredData;

    const { current, pageSize } = pagination;
    const startIndex = (current - 1) * pageSize;
    return filteredData.slice(startIndex, startIndex + pageSize);
  }, [filteredData, pagination]);

  // Handle sort
  const handleSort = useCallback(
    (key: string) => {
      const newSortConfig =
        sortConfig?.key === key && sortConfig.order === "asc"
          ? { key, order: "desc" as const }
          : { key, order: "asc" as const };

      setSortConfig(newSortConfig);
      onSort?.(newSortConfig);
    },
    [sortConfig, onSort]
  );

  // Handle filter
  const handleFilter = useCallback(
    (key: string, value: any) => {
      const newFilters = { ...filters, [key]: value };
      setFilters(newFilters);
      onFilter?.(newFilters);
    },
    [filters, onFilter]
  );

  // Handle row selection
  const handleRowSelection = useCallback(
    (rowKey: string, checked: boolean) => {
      if (!rowSelection) return;

      const newSelectedKeys = checked
        ? [...rowSelection.selectedRowKeys, rowKey]
        : rowSelection.selectedRowKeys.filter((key) => key !== rowKey);

      const selectedRows = data.filter((record, index) =>
        newSelectedKeys.includes(getRowKey(record, index))
      );

      rowSelection.onChange(newSelectedKeys, selectedRows);
    },
    [rowSelection, data, getRowKey]
  );

  // Handle expand
  const handleExpand = useCallback(
    (rowKey: string) => {
      const newExpanded = new Set(expandedRows);
      if (newExpanded.has(rowKey)) {
        newExpanded.delete(rowKey);
      } else {
        newExpanded.add(rowKey);
      }
      setExpandedRows(newExpanded);
    },
    [expandedRows]
  );

  const renderSortIcon = (column: Column<T>) => {
    if (!column.sortable) return null;

    const isActive = sortConfig?.key === column.key;
    const direction = isActive ? sortConfig.order : null;

    return (
      <button
        onClick={() => handleSort(String(column.key))}
        className="ml-1 inline-flex items-center"
        aria-label={`Sort by ${column.title}`}
      >
        <svg
          className={`w-4 h-4 transition-colors ${
            isActive ? "text-blue-500" : "text-gray-400 hover:text-gray-600"
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d={direction === "asc" ? "M5 15l7-7 7 7" : "M19 9l-7 7-7-7"}
          />
        </svg>
      </button>
    );
  };

  const renderCell = (column: Column<T>, record: T, index: number) => {
    const value = record[column.key as keyof T];
    const content = column.render ? column.render(value, record, index) : value;

    return (
      <td
        key={String(column.key)}
        className={`
          px-4 py-3 border-b border-gray-200
          ${sizeStyles[size]}
        `}
        style={{
          width: column.width,
          color: theme.colors.text,
        }}
      >
        {content}
      </td>
    );
  };

  const renderExpandableRow = (record: T, index: number) => {
    if (!expandable || !expandedRows.has(getRowKey(record, index))) return null;

    return (
      <tr key={`expanded-${getRowKey(record, index)}`}>
        <td
          colSpan={
            columns.length + (rowSelection ? 1 : 0) + (expandable ? 1 : 0)
          }
          className="bg-gray-50 px-4 py-4"
        >
          {expandable.expandedRowRender(record, index)}
        </td>
      </tr>
    );
  };

  const renderLoadingOverlay = () => {
    if (!loading) return null;

    return (
      <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
          <span className="text-gray-600">Loading...</span>
        </div>
      </div>
    );
  };

  const tableClasses = `
    w-full border-collapse
    ${bordered ? "border border-gray-300" : ""}
    ${className}
  `;

  const tableContainerClasses = `
    relative overflow-auto
    ${scroll?.x ? "" : "overflow-x-auto"}
    ${scroll?.y ? "max-h-96 overflow-y-auto" : ""}
  `;

  return (
    <div className={tableContainerClasses} style={style}>
      {renderLoadingOverlay()}

      <table
        className={tableClasses}
        data-testid={testId}
        style={{
          minWidth: scroll?.x,
        }}
      >
        <thead className="bg-gray-50">
          <tr>
            {/* Selection column */}
            {rowSelection && (
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  checked={
                    rowSelection.selectedRowKeys.length === paginatedData.length
                  }
                  onChange={(e) => {
                    const checked = e.target.checked;
                    const allKeys = paginatedData.map((record, index) =>
                      getRowKey(record, index)
                    );
                    const newSelectedKeys = checked
                      ? [
                          ...new Set([
                            ...rowSelection.selectedRowKeys,
                            ...allKeys,
                          ]),
                        ]
                      : rowSelection.selectedRowKeys.filter(
                          (key) => !allKeys.includes(key)
                        );

                    const selectedRows = data.filter((record, index) =>
                      newSelectedKeys.includes(getRowKey(record, index))
                    );

                    rowSelection.onChange(newSelectedKeys, selectedRows);
                  }}
                />
              </th>
            )}

            {/* Expand column */}
            {expandable && (
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {/* Empty header for expand column */}
              </th>
            )}

            {/* Data columns */}
            {columns.map((column) => (
              <th
                key={String(column.key)}
                className={`
                  px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider
                  ${column.sortable ? "cursor-pointer hover:bg-gray-100" : ""}
                `}
                style={{
                  width: column.width,
                  minWidth: column.width,
                }}
                onClick={() =>
                  column.sortable && handleSort(String(column.key))
                }
              >
                <div className="flex items-center">
                  <span>{column.title}</span>
                  {renderSortIcon(column)}
                </div>
              </th>
            ))}
          </tr>
        </thead>

        <tbody className="bg-white divide-y divide-gray-200">
          {paginatedData.map((record, index) => {
            const rowKeyValue = getRowKey(record, index);
            const isSelected =
              rowSelection?.selectedRowKeys.includes(rowKeyValue);
            const isExpandable = expandable?.rowExpandable?.(record) ?? true;

            return (
              <React.Fragment key={rowKeyValue}>
                <tr
                  className={`
                    ${striped && index % 2 === 1 ? "bg-gray-50" : ""}
                    ${hoverable ? "hover:bg-gray-50" : ""}
                    ${isSelected ? "bg-blue-50" : ""}
                  `}
                >
                  {/* Selection checkbox */}
                  {rowSelection && (
                    <td className="px-4 py-3">
                      <input
                        type="checkbox"
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        checked={isSelected}
                        disabled={
                          rowSelection.getCheckboxProps?.(record)?.disabled
                        }
                        onChange={(e) =>
                          handleRowSelection(rowKeyValue, e.target.checked)
                        }
                      />
                    </td>
                  )}

                  {/* Expand button */}
                  {expandable && (
                    <td className="px-4 py-3">
                      {isExpandable && (
                        <button
                          onClick={() => handleExpand(rowKeyValue)}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          <svg
                            className={`w-5 h-5 transition-transform ${
                              expandedRows.has(rowKeyValue) ? "rotate-90" : ""
                            }`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 5l7 7-7 7"
                            />
                          </svg>
                        </button>
                      )}
                    </td>
                  )}

                  {/* Data cells */}
                  {columns.map((column) => renderCell(column, record, index))}
                </tr>

                {/* Expanded row */}
                {renderExpandableRow(record, index)}
              </React.Fragment>
            );
          })}
        </tbody>
      </table>

      {/* Pagination */}
      {pagination && (
        <div className="flex items-center justify-between px-4 py-3 bg-white border-t border-gray-200">
          <div className="text-sm text-gray-700">
            Showing {(pagination.current - 1) * pagination.pageSize + 1} to{" "}
            {Math.min(
              pagination.current * pagination.pageSize,
              pagination.total
            )}{" "}
            of {pagination.total} results
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() =>
                pagination.onChange(
                  Math.max(1, pagination.current - 1),
                  pagination.pageSize
                )
              }
              disabled={pagination.current === 1}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>

            <span className="text-sm text-gray-700">
              Page {pagination.current} of{" "}
              {Math.ceil(pagination.total / pagination.pageSize)}
            </span>

            <button
              onClick={() =>
                pagination.onChange(
                  Math.min(
                    Math.ceil(pagination.total / pagination.pageSize),
                    pagination.current + 1
                  ),
                  pagination.pageSize
                )
              }
              disabled={
                pagination.current ===
                Math.ceil(pagination.total / pagination.pageSize)
              }
              className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Table;
