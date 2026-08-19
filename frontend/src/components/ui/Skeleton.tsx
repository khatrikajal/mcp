import * as React from "react";
import { cn } from "../../lib/cn";

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "text" | "circular" | "rectangular";
  width?: string | number;
  height?: string | number;
  animate?: boolean;
}

export function Skeleton({
  className,
  variant = "rectangular",
  width,
  height,
  animate = true,
  ...props
}: SkeletonProps) {
  const variantStyles = {
    text: "rounded",
    circular: "rounded-full",
    rectangular: "rounded-md",
  };

  return (
    <div
      className={cn(
        "bg-slate-200 dark:bg-slate-700",
        animate && "animate-pulse",
        variantStyles[variant],
        className
      )}
      style={{
        width: typeof width === "number" ? `${width}px` : width,
        height: typeof height === "number" ? `${height}px` : height,
      }}
      role="status"
      aria-label="Loading..."
      {...props}
    />
  );
}

// Pre-built skeleton patterns
export function CardSkeleton() {
  return (
    <div className="rounded-lg border bg-card p-4 space-y-4">
      <div className="flex justify-between items-start">
        <div className="space-y-2">
          <Skeleton width={180} height={20} />
          <Skeleton width={120} height={14} />
        </div>
        <Skeleton width={80} height={24} variant="text" />
      </div>
      <Skeleton width="100%" height={60} />
      <div className="flex gap-2">
        <Skeleton width={100} height={32} />
        <Skeleton width={100} height={32} />
      </div>
    </div>
  );
}

export function TableRowSkeleton({ columns = 5 }: { columns?: number }) {
  return (
    <tr className="border-b">
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="p-4">
          <Skeleton width={i === 0 ? 150 : 80} height={16} />
        </td>
      ))}
    </tr>
  );
}

export function ListItemSkeleton() {
  return (
    <div className="flex items-center gap-4 p-4 border-b">
      <Skeleton width={40} height={40} variant="circular" />
      <div className="flex-1 space-y-2">
        <Skeleton width="60%" height={16} />
        <Skeleton width="40%" height={12} />
      </div>
    </div>
  );
}

export function DelegationCardSkeleton() {
  return (
    <div className="rounded-lg border bg-card p-4 space-y-4 animate-pulse">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="space-y-2 flex-1">
          <Skeleton width="70%" height={22} />
          <Skeleton width="50%" height={14} />
        </div>
        <div className="flex flex-col items-end gap-1">
          <Skeleton width={80} height={22} variant="text" />
          <Skeleton width={100} height={22} variant="text" />
        </div>
      </div>

      {/* Description */}
      <Skeleton width="100%" height={40} />

      {/* Attendees */}
      <div className="flex gap-2">
        <Skeleton width={60} height={20} variant="text" />
        <Skeleton width={60} height={20} variant="text" />
        <Skeleton width={60} height={20} variant="text" />
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-2">
        <Skeleton width={100} height={36} />
        <Skeleton width={100} height={36} />
      </div>
    </div>
  );
}

export function StatCardSkeleton() {
  return (
    <div className="rounded-lg border bg-card p-4 animate-pulse">
      <div className="flex items-center gap-2 mb-2">
        <Skeleton width={20} height={20} variant="circular" />
        <Skeleton width={60} height={14} />
      </div>
      <Skeleton width={40} height={28} />
    </div>
  );
}
