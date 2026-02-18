"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Search,
  Users,
  Loader2,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui";
import { formatDate } from "@/lib/utils";
import api from "@/lib/api";

interface User {
  id: number;
  username: string;
  email: string;
  fullName: string | null;
  phone: string | null;
  role: string;
  isVerified: boolean;
  isActive: boolean;
  isBlocked: boolean;
  lastLoginAt: string | null;
  createdAt: string;
}

interface UserStats {
  totalUsers: number;
  activeUsers: number;
  blockedUsers: number;
  adminUsers: number;
  newUsersToday: number;
  newUsersWeek: number;
}

const ROLE_COLORS: Record<string, { bg: string; text: string }> = {
  admin: { bg: "bg-primary/20", text: "text-primary" },
  user: { bg: "bg-foreground-muted/20", text: "text-foreground-muted" },
};

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });
      if (search) params.append("search", search);

      const [usersRes, statsRes] = await Promise.all([
        api.get(`/admin/users?${params}`),
        api.get("/admin/users/stats"),
      ]);

      setUsers(usersRes.data.users);
      setTotal(usersRes.data.total);
      setStats(statsRes.data);
    } catch (err) {
      console.error("Failed to fetch users:", err);
    } finally {
      setIsLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Users</h1>
        <p className="text-foreground-muted">
          View platform users
        </p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-foreground">
                {stats.totalUsers}
              </p>
              <p className="text-sm text-foreground-muted">Total Users</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-primary">
                {stats.adminUsers}
              </p>
              <p className="text-sm text-foreground-muted">Admins</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-foreground">
                {stats.newUsersToday}
              </p>
              <p className="text-sm text-foreground-muted">New Today</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4 text-center">
              <p className="text-2xl font-bold text-foreground">
                {stats.newUsersWeek}
              </p>
              <p className="text-sm text-foreground-muted">This Week</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Search */}
      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-muted" />
            <input
              type="text"
              placeholder="Search by name, email, or username..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-10 pr-4 py-2 bg-background-elevated border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : users.length === 0 ? (
            <div className="text-center py-12">
              <Users className="h-12 w-12 text-foreground-muted mx-auto mb-4" />
              <p className="text-foreground-muted">No users found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left p-4 text-sm font-medium text-foreground-muted">
                      User
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-foreground-muted">
                      Role
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-foreground-muted">
                      Last Login
                    </th>
                    <th className="text-left p-4 text-sm font-medium text-foreground-muted">
                      Joined
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr
                      key={user.id}
                      className="border-b border-border last:border-0 hover:bg-background-soft"
                    >
                      <td className="p-4">
                        <div>
                          <p className="font-medium text-foreground">
                            {user.fullName || user.username}
                          </p>
                          <p className="text-sm text-foreground-muted">
                            {user.email}
                          </p>
                          {user.phone && (
                            <p className="text-xs text-foreground-muted">
                              {user.phone}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="p-4">
                        <span
                          className={`inline-flex px-2 py-1 rounded-full text-xs font-medium capitalize ${
                            ROLE_COLORS[user.role]?.bg || "bg-gray-100"
                          } ${ROLE_COLORS[user.role]?.text || "text-gray-800"}`}
                        >
                          {user.role}
                        </span>
                      </td>
                      <td className="p-4">
                        <p className="text-foreground-muted text-sm">
                          {user.lastLoginAt
                            ? formatDate(user.lastLoginAt)
                            : "Never"}
                        </p>
                      </td>
                      <td className="p-4">
                        <p className="text-foreground-muted text-sm">
                          {user.createdAt ? formatDate(user.createdAt) : "-"}
                        </p>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-foreground-muted">
            Showing {(page - 1) * pageSize + 1} to{" "}
            {Math.min(page * pageSize, total)} of {total} users
          </p>
          <div className="flex gap-2">
            <button
              className="px-4 py-2 text-sm border border-border rounded-lg disabled:opacity-50"
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
            >
              Previous
            </button>
            <button
              className="px-4 py-2 text-sm border border-border rounded-lg disabled:opacity-50"
              disabled={page === totalPages}
              onClick={() => setPage(page + 1)}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
