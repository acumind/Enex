"use client";

import { useCallback, useEffect, useState } from "react";
import { UserPlus, UserCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import { api, ApiClientError } from "@/lib/api-client";
import type { FollowCheckResponse } from "@/lib/types";

interface Props {
  predictorId: string;
}

export function FollowButton({ predictorId }: Props) {
  const { isAuthenticated } = useAuth();
  const [following, setFollowing] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) return;
    api
      .get<FollowCheckResponse>(`/following/check/${predictorId}`)
      .then((data) => setFollowing(data.following))
      .catch(() => {});
  }, [isAuthenticated, predictorId]);

  const toggle = useCallback(async () => {
    setLoading(true);
    try {
      if (following) {
        await api.delete(`/following/${predictorId}`);
        setFollowing(false);
      } else {
        await api.post("/following", { predictor_id: predictorId });
        setFollowing(true);
      }
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 409) {
        setFollowing(true);
      }
    } finally {
      setLoading(false);
    }
  }, [following, predictorId]);

  if (!isAuthenticated) return null;

  return (
    <Button
      variant={following ? "secondary" : "outline"}
      size="sm"
      onClick={toggle}
      disabled={loading}
    >
      {following ? (
        <>
          <UserCheck className="mr-1.5 h-4 w-4" />
          Following
        </>
      ) : (
        <>
          <UserPlus className="mr-1.5 h-4 w-4" />
          Follow
        </>
      )}
    </Button>
  );
}
