"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Bell } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api-client";
import type {
  NotificationResponse,
  PaginatedResponse,
  UnreadCountResponse,
} from "@/lib/types";

export function NotificationBell() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationResponse[]>(
    [],
  );
  const ref = useRef<HTMLDivElement>(null);

  // Poll unread count
  useEffect(() => {
    if (!isAuthenticated) return;
    const fetchCount = () => {
      api
        .get<UnreadCountResponse>("/notifications/unread-count")
        .then((data) => setUnread(data.count))
        .catch(() => {});
    };
    fetchCount();
    const interval = setInterval(fetchCount, 30_000);
    return () => clearInterval(interval);
  }, [isAuthenticated]);

  // Load recent notifications when dropdown opens
  useEffect(() => {
    if (!open) return;
    api
      .get<PaginatedResponse<NotificationResponse>>("/notifications", {
        limit: "5",
      })
      .then((data) => setNotifications(data.items))
      .catch(() => {});
  }, [open]);

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const markRead = useCallback(
    async (n: NotificationResponse) => {
      if (!n.is_read) {
        await api.post(`/notifications/${n.id}/read`).catch(() => {});
        setUnread((prev) => Math.max(0, prev - 1));
        setNotifications((prev) =>
          prev.map((item) =>
            item.id === n.id ? { ...item, is_read: true } : item,
          ),
        );
      }
      // Navigate based on notification data
      if (n.data.stock_symbol) {
        router.push(`/stock/${n.data.stock_symbol}`);
      } else if (n.data.predictor_slug) {
        router.push(`/predictor/${n.data.predictor_slug}`);
      }
      setOpen(false);
    },
    [router],
  );

  const markAllRead = useCallback(async () => {
    await api.post("/notifications/read-all").catch(() => {});
    setUnread(0);
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
  }, []);

  if (!isAuthenticated) return null;

  return (
    <div className="relative" ref={ref}>
      <Button
        variant="ghost"
        size="sm"
        className="relative"
        onClick={() => setOpen((prev) => !prev)}
      >
        <Bell className="h-5 w-5" />
        {unread > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
            {unread > 99 ? "99+" : unread}
          </span>
        )}
      </Button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-80 overflow-hidden rounded-lg border bg-popover shadow-lg">
          <div className="flex items-center justify-between border-b px-4 py-2">
            <p className="text-sm font-semibold">Notifications</p>
            {unread > 0 && (
              <button
                onClick={markAllRead}
                className="text-xs text-primary hover:underline"
              >
                Mark all as read
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <p className="px-4 py-6 text-center text-sm text-muted-foreground">
                No notifications
              </p>
            ) : (
              notifications.map((n) => (
                <button
                  key={n.id}
                  onClick={() => markRead(n)}
                  className={`block w-full px-4 py-3 text-left hover:bg-muted/50 ${
                    !n.is_read ? "bg-muted/20" : ""
                  }`}
                >
                  <p className="text-sm font-medium">{n.title}</p>
                  {n.message && (
                    <p className="mt-0.5 text-xs text-muted-foreground line-clamp-2">
                      {n.message}
                    </p>
                  )}
                  <p className="mt-1 text-[10px] text-muted-foreground">
                    {new Date(n.created_at).toLocaleString()}
                  </p>
                </button>
              ))
            )}
          </div>
          <div className="border-t px-4 py-2 text-center">
            <Link
              href="/notifications"
              className="text-xs text-primary hover:underline"
              onClick={() => setOpen(false)}
            >
              View all notifications
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
