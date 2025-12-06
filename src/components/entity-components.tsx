//F:\nodebase_final_pro\src\components\entity-components.tsx
"use client";

import React, { useRef, useState, useEffect } from "react";
import Link from "next/link"; // ✅ Use Next.js Link
import {
  PlusIcon,
  SearchIcon,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Inbox,
  AlertCircle,
  SearchX,
  CircleX,
  MoreVertical,
  Trash,
} from "lucide-react";

// --- SHADCN IMPORTS ---
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";

// ------------------------------------------------------------------
// 1. ENTITY CONTAINER
// ------------------------------------------------------------------
interface EntityContainerProps {
  children: React.ReactNode;
  header?: React.ReactNode;
  search?: React.ReactNode;
  pagination?: React.ReactNode;
}

export const EntityContainer = ({
  children,
  header,
  search,
  pagination,
}: EntityContainerProps) => {
  return (
    <div className="p-4 md:px-8 md:py-8 h-full bg-background min-h-screen">
      <div className="mx-auto max-w-7xl w-full flex flex-col gap-y-8 h-full">
        {header}
        <div className="flex flex-col gap-y-6 h-full min-h-[50vh]">
          {search}
          {children}
        </div>
        {pagination}
      </div>
    </div>
  );
};

// ------------------------------------------------------------------
// 2. ENTITY HEADER
// ------------------------------------------------------------------
type EntityHeaderProps = {
  title: string;
  description?: string;
  newButtonLabel?: string;
  disabled?: boolean;
  isCreating?: boolean;
} & (
  | { onNew: () => void; newButtonHref?: never }
  | { newButtonHref: string; onNew?: never }
  | { onNew?: never; newButtonHref?: never }
);

export const EntityHeader = ({
  title,
  description,
  onNew,
  newButtonHref,
  newButtonLabel = "Create New",
  disabled,
  isCreating,
}: EntityHeaderProps) => {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          {title}
        </h1>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </div>

      {/* Button Actions */}
      <div>
        {onNew && !newButtonHref && (
          <Button disabled={isCreating || disabled} size="sm" onClick={onNew}>
            {isCreating ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <PlusIcon className="mr-2 h-4 w-4" />
            )}
            {newButtonLabel}
          </Button>
        )}
        {newButtonHref && !onNew && (
          <Link href={newButtonHref}>
            <Button disabled={isCreating || disabled} size="sm">
              <PlusIcon className="mr-2 h-4 w-4" />
              {newButtonLabel}
            </Button>
          </Link>
        )}
      </div>
    </div>
  );
};

// ------------------------------------------------------------------
// 3. ENTITY SEARCH
// ------------------------------------------------------------------
export interface EntitySearchProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export const EntitySearch = ({
  value,
  onChange,
  placeholder,
}: EntitySearchProps) => {
  const [isExpanded, setIsExpanded] = useState(!!value);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isExpanded && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isExpanded]);

  const handleClear = () => {
    onChange("");
    if (inputRef.current) inputRef.current.focus();
  };

  return (
    <div
      className={cn(
        "relative flex items-center transition-all duration-300 ease-in-out h-10",
        isExpanded ? "w-full max-w-sm" : "w-10"
      )}>
      <SearchIcon
        className={cn(
          "absolute left-3 h-4 w-4 text-muted-foreground z-10 cursor-pointer transition-colors",
          !isExpanded && "hover:text-foreground"
        )}
        onClick={() => setIsExpanded(true)}
      />

      <Input
        ref={inputRef}
        type="text"
        placeholder={placeholder ?? "Search..."}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onBlur={() => !value && setIsExpanded(false)}
        className={cn(
          "pl-9 pr-9 h-full transition-all duration-300 ease-in-out",
          isExpanded
            ? "w-full opacity-100 border-input"
            : "w-0 opacity-0 border-transparent p-0 overflow-hidden"
        )}
      />

      {value && isExpanded && (
        <button
          type="button"
          onClick={handleClear}
          className="absolute right-3 text-muted-foreground hover:text-foreground focus:outline-none">
          <CircleX className="h-4 w-4" />
        </button>
      )}
    </div>
  );
};

// ------------------------------------------------------------------
// 4. ENTITY ITEM (Grid/List Card)
// ------------------------------------------------------------------
interface EntityItemProps {
  href: string;
  title: string;
  subtitle?: React.ReactNode;
  image?: React.ReactNode;
  actions?: React.ReactNode;
  onRemove?: () => void | Promise<void>;
  isRemoving?: boolean;
  className?: string;
  variant?: "grid" | "list";
}

export const EntityItem = ({
  href,
  title,
  subtitle,
  image,
  actions,
  onRemove,
  isRemoving,
  className,
  variant = "grid",
}: EntityItemProps) => {
  const handleRemove = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (onRemove) {
      await onRemove();
    }
  };

  return (
    <Link href={href} className={cn("block h-full outline-none", className)}>
      <Card
        className={cn(
          "relative group transition-all h-full overflow-hidden hover:shadow-md hover:border-foreground/20",
          isRemoving && "opacity-50 pointer-events-none"
        )}>
        {/* Loading Overlay for Deletion */}
        {isRemoving && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/50 z-10">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}

        <CardContent
          className={cn(
            "p-0",
            variant === "list"
              ? "flex flex-row items-center justify-between p-4"
              : "flex flex-col h-full"
          )}>
          {/* Main Info */}
          <div
            className={cn(
              "flex items-center gap-4 w-full",
              variant === "grid" && "p-6 pb-3 flex-col items-start gap-4"
            )}>
            {image && <div className="flex-shrink-0">{image}</div>}

            <div className="space-y-1 w-full overflow-hidden">
              <CardTitle className="text-base font-medium truncate">
                {title}
              </CardTitle>
              {subtitle && (
                <CardDescription className="text-xs truncate">
                  {subtitle}
                </CardDescription>
              )}
            </div>
          </div>

          {/* Actions & Menu */}
          {(actions || onRemove) && (
            <div
              className={cn(
                "flex items-center gap-2",
                variant === "grid" &&
                  "mt-auto p-6 pt-0 w-full justify-end border-t bg-muted/20 pt-3"
              )}
              onClick={(e) => e.preventDefault()} // Prevent link click when clicking actions
            >
              {actions}

              {onRemove && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-foreground">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      onClick={handleRemove}
                      className="text-destructive focus:text-destructive cursor-pointer">
                      <Trash className="mr-2 h-4 w-4" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
};

// ------------------------------------------------------------------
// 5. ENTITY PAGINATION
// ------------------------------------------------------------------
export interface EntityPaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  disabled?: boolean;
}

export const EntityPagination = ({
  page,
  totalPages,
  onPageChange,
  disabled,
}: EntityPaginationProps) => {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between border-t pt-4 mt-4 w-full">
      <div className="text-sm text-muted-foreground">
        Page {page} of {totalPages}
      </div>

      <Pagination className="w-auto mx-0">
        <PaginationContent>
          <PaginationItem>
            <PaginationPrevious
              onClick={() => page > 1 && onPageChange(page - 1)}
              aria-disabled={page <= 1 || disabled}
              className={cn(
                "cursor-pointer",
                (page <= 1 || disabled) && "pointer-events-none opacity-50"
              )}
            />
          </PaginationItem>

          <PaginationItem>
            <PaginationNext
              onClick={() => page < totalPages && onPageChange(page + 1)}
              aria-disabled={page >= totalPages || disabled}
              className={cn(
                "cursor-pointer",
                (page >= totalPages || disabled) &&
                  "pointer-events-none opacity-50"
              )}
            />
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    </div>
  );
};

// ------------------------------------------------------------------
// 6. STATE VIEWS (Empty, Error, Loading, No Results)
// ------------------------------------------------------------------
interface StateViewProps {
  message?: string;
  title?: string;
  action?: React.ReactNode;
}

interface LoadingViewProps extends StateViewProps {
  entity?: string;
}

export const LoadingView = ({
  entity = "items",
  message,
}: LoadingViewProps) => {
  return (
    <div className="w-full space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-8 w-[200px]" />
        <Skeleton className="h-8 w-[100px]" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-[200px] w-full rounded-xl" />
        ))}
      </div>
    </div>
  );
};

export const EmptyView = ({
  entity = "items",
  message,
  title,
  action,
}: LoadingViewProps) => {
  return (
    <Card className="flex flex-col items-center justify-center p-8 text-center border-dashed shadow-none bg-background h-full min-h-[400px]">
      <CardHeader className="flex flex-col items-center pb-2">
        <div className="flex size-14 items-center justify-center rounded-full bg-muted/50 mb-2">
          <Inbox className="size-7 text-muted-foreground" />
        </div>
        <CardTitle className="text-xl">{title || `No ${entity}`}</CardTitle>
      </CardHeader>
      <CardContent>
        <CardDescription className="text-base max-w-[350px]">
          {message ||
            `You haven't created any ${entity} yet. Get started by creating your first one.`}
        </CardDescription>
      </CardContent>
      {action && <CardFooter>{action}</CardFooter>}
    </Card>
  );
};

export const ErrorView = ({ message, title, action }: StateViewProps) => {
  return (
    <Card className="flex flex-col items-center justify-center p-8 text-center border-destructive/30 shadow-sm bg-destructive/5 h-full min-h-[400px]">
      <CardHeader className="flex flex-col items-center pb-2">
        <div className="flex size-14 items-center justify-center rounded-full bg-destructive/10 mb-2">
          <AlertCircle className="size-7 text-destructive" />
        </div>
        <CardTitle className="text-xl text-destructive">
          {title || "Something went wrong"}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <CardDescription className="text-base max-w-[350px] text-destructive/80">
          {message ||
            "We encountered an error while loading data. Please try again."}
        </CardDescription>
      </CardContent>
      {action && <CardFooter>{action}</CardFooter>}
    </Card>
  );
};

export const NoResultsView = ({ message, title, action }: StateViewProps) => {
  return (
    <Card className="flex flex-col items-center justify-center p-8 text-center border-none shadow-none bg-transparent h-full min-h-[300px]">
      <CardHeader className="flex flex-col items-center pb-2">
        <div className="flex size-12 items-center justify-center rounded-full bg-muted mb-2">
          <SearchX className="size-6 text-muted-foreground" />
        </div>
        <CardTitle className="text-lg">{title || "No results found"}</CardTitle>
      </CardHeader>
      <CardContent>
        <CardDescription className="max-w-[300px]">
          {message ||
            "We couldn't find anything matching your search. Try adjusting your filters."}
        </CardDescription>
      </CardContent>
      {action && <CardFooter>{action}</CardFooter>}
    </Card>
  );
};
