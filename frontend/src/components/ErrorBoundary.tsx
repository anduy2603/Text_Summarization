import { Component, type ErrorInfo, type ReactNode } from "react";
import { MaterialIcon } from "./icons/MaterialIcon";

type Props = { children: ReactNode };
type State = { error: Error | null };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[ErrorBoundary]", error.message, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex h-screen flex-col items-center justify-center gap-4 bg-background p-8 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-red-50">
            <MaterialIcon name="error" className="text-error" size="lg" />
          </div>
          <div>
            <p className="text-base font-semibold text-on-surface">Đã xảy ra lỗi không mong muốn</p>
            <p className="mt-1 max-w-xs text-sm text-on-surface-variant">
              {this.state.error.message}
            </p>
          </div>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="rounded-xl bg-primary px-6 py-2.5 text-sm font-semibold text-white transition-all active:scale-[0.97]"
          >
            Tải lại trang
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
