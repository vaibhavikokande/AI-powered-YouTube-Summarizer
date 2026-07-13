import { Moon, Sun } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/auth-store";

export function Header({ isDark, onToggleDark }: { isDark: boolean; onToggleDark: () => void }) {
  const { user, isAuthenticated, logout } = useAuthStore();
  const navigate = useNavigate();

  return (
    <header className="border-b border-border">
      <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
        <Link to="/" className="font-semibold">
          AI YouTube Summarizer
        </Link>
        <nav className="flex items-center gap-3 text-sm">
          {isAuthenticated && (
            <Link to="/history" className="text-muted-foreground hover:text-foreground">
              History
            </Link>
          )}
          <Button variant="ghost" size="icon" onClick={onToggleDark}>
            {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
          {isAuthenticated ? (
            <>
              <span className="text-muted-foreground">{user?.email}</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  logout();
                  navigate("/");
                }}
              >
                Log out
              </Button>
            </>
          ) : (
            <Link to="/login">
              <Button size="sm">Log in</Button>
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
