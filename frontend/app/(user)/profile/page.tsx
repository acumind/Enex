"use client";

import { useCallback, useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/lib/auth-context";
import { api, ApiClientError } from "@/lib/api-client";
import type { AuthUser } from "@/lib/types";

function maskPhone(phone: string): string {
  if (phone.length < 6) return phone;
  return phone.slice(0, 3) + "****" + phone.slice(-4);
}

export default function ProfilePage() {
  const router = useRouter();
  const { user, logout, login, accessToken } = useAuth();
  const [editingName, setEditingName] = useState(false);
  const [nameInput, setNameInput] = useState(user?.name || "");
  const [saving, setSaving] = useState(false);

  const handleSaveName = useCallback(async () => {
    if (!nameInput.trim()) return;
    setSaving(true);
    try {
      const updated = await api.patch<AuthUser>("/auth/me", {
        name: nameInput.trim(),
      });
      if (accessToken) login(accessToken, updated);
      setEditingName(false);
    } catch (e) {
      if (e instanceof ApiClientError) {
        alert(e.message);
      }
    } finally {
      setSaving(false);
    }
  }, [nameInput, accessToken, login]);

  const handleLogout = useCallback(async () => {
    await logout();
    router.replace("/login");
  }, [logout, router]);

  if (!user) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">Loading profile...</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl p-6">
      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Your account details</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Avatar */}
          {user.avatar_url && (
            <div className="flex items-center gap-4">
              <Image
                src={user.avatar_url}
                alt="Avatar"
                width={64}
                height={64}
                className="rounded-full"
                unoptimized
              />
            </div>
          )}

          {/* Name */}
          <div className="space-y-1">
            <Label>Name</Label>
            {editingName ? (
              <div className="flex gap-2">
                <Input
                  value={nameInput}
                  onChange={(e) => setNameInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSaveName()}
                  autoFocus
                />
                <Button onClick={handleSaveName} disabled={saving} size="sm">
                  {saving ? "..." : "Save"}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setEditingName(false);
                    setNameInput(user.name || "");
                  }}
                >
                  Cancel
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <p className="text-sm">{user.name || "Not set"}</p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setNameInput(user.name || "");
                    setEditingName(true);
                  }}
                >
                  Edit
                </Button>
              </div>
            )}
          </div>

          {/* Email */}
          <div className="space-y-1">
            <Label>Email</Label>
            <div className="flex items-center gap-2">
              <p className="text-sm">{user.email || "Not set"}</p>
              {user.email && (
                <Badge variant={user.is_email_verified ? "default" : "secondary"}>
                  {user.is_email_verified ? "Verified" : "Unverified"}
                </Badge>
              )}
            </div>
          </div>

          {/* Phone */}
          <div className="space-y-1">
            <Label>Phone</Label>
            <div className="flex items-center gap-2">
              <p className="text-sm">
                {user.phone ? maskPhone(user.phone) : "Not set"}
              </p>
              {user.phone && (
                <Badge variant={user.is_phone_verified ? "default" : "secondary"}>
                  {user.is_phone_verified ? "Verified" : "Unverified"}
                </Badge>
              )}
            </div>
          </div>

          {/* Role */}
          <div className="space-y-1">
            <Label>Role</Label>
            <Badge variant="outline" className="capitalize">
              {user.role}
            </Badge>
          </div>

          {/* Auth Methods */}
          <div className="space-y-1">
            <Label>Sign-in Methods</Label>
            <div className="flex gap-2">
              {user.auth_methods.map((method) => (
                <Badge key={method} variant="secondary" className="capitalize">
                  {method}
                </Badge>
              ))}
              {user.auth_methods.length === 0 && (
                <p className="text-sm text-muted-foreground">None</p>
              )}
            </div>
          </div>

          {/* Member since */}
          <div className="space-y-1">
            <Label>Member Since</Label>
            <p className="text-sm text-muted-foreground">
              {new Date(user.created_at).toLocaleDateString()}
            </p>
          </div>

          {/* Logout */}
          <div className="pt-4 border-t">
            <Button variant="destructive" onClick={handleLogout}>
              Sign Out
            </Button>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
