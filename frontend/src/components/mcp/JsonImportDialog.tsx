import { useState } from "react";
import { createPortal } from "react-dom";
import { Loader2, X, FileJson, CheckCircle2, AlertCircle } from "lucide-react";
import { importMcpServers } from "../../services/api";
import type { McpImportResult } from "../../types";

interface JsonImportDialogProps {
  open: boolean;
  onClose: () => void;
  onImported: () => void;
}

const JsonImportDialog: React.FC<JsonImportDialogProps> = ({ open, onClose, onImported }) => {
  const [jsonText, setJsonText] = useState("");
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<McpImportResult | null>(null);
  const [jsonError, setJsonError] = useState<string | null>(null);

  if (!open) return null;

  const handleTextChange = (text: string) => {
    setJsonText(text);
    setResult(null);
    if (text.trim()) {
      try {
        JSON.parse(text);
        setJsonError(null);
      } catch (e) {
        setJsonError(e instanceof SyntaxError ? e.message : "JSON 格式无效");
      }
    } else {
      setJsonError(null);
    }
  };

  const handleImport = async () => {
    if (!jsonText.trim() || jsonError) return;
    try {
      setImporting(true);
      const res = await importMcpServers(jsonText, true);
      setResult(res);
      if (res.created_count > 0) {
        onImported();
      }
    } catch (e) {
      setJsonError(e instanceof Error ? e.message : "导入失败");
    } finally {
      setImporting(false);
    }
  };

  const handleClose = () => {
    setJsonText("");
    setResult(null);
    setJsonError(null);
    onClose();
  };

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      onClick={handleClose}
    >
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative mx-4 flex w-full max-w-2xl flex-col rounded-2xl glass-card shadow-2xl"
        style={{
          border: "1px solid var(--glass-border)",
          maxHeight: "80vh",
        }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-6 py-4"
          style={{ borderBottom: "1px solid var(--glass-border)" }}
        >
          <div className="flex items-center gap-3">
            <FileJson size={22} style={{ color: "var(--accent-primary)" }} />
            <h2 className="text-lg font-semibold" style={{ color: "var(--text-primary)" }}>
              JSON 导入 MCP 配置
            </h2>
          </div>
          <button
            type="button"
            onClick={handleClose}
            className="rounded-lg p-1.5 transition-colors hover:bg-white/10"
            style={{ color: "var(--text-muted)" }}
            aria-label="关闭"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {!result ? (
            <>
              <p className="mb-3 text-sm" style={{ color: "var(--text-secondary)" }}>
                粘贴 MCP 配置 JSON，支持 Claude Desktop、VS Code 等常见格式。
              </p>
              <textarea
                value={jsonText}
                onChange={(e) => handleTextChange(e.target.value)}
                placeholder={`{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
    }
  }
}`}
                className="w-full rounded-xl px-4 py-3 font-mono text-sm"
                style={{
                  backgroundColor: "var(--surface-subtle)",
                  border: `1px solid ${jsonError ? "var(--status-danger)" : "var(--glass-border)"}`,
                  color: "var(--text-primary)",
                  minHeight: "220px",
                  resize: "vertical",
                }}
                spellCheck={false}
              />
              {jsonError && (
                <p className="mt-2 flex items-center gap-1.5 text-xs" style={{ color: "var(--status-danger)" }}>
                  <AlertCircle size={14} />
                  {jsonError}
                </p>
              )}
            </>
          ) : (
            <div>
              <div className="mb-4 flex items-center gap-2">
                <CheckCircle2 size={20} style={{ color: "var(--status-success)" }} />
                <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                  导入完成：成功 {result.created_count} 个
                  {result.skipped_count > 0 && `，跳过 ${result.skipped_count} 个（同名已存在）`}
                  {result.errors.length > 0 && `，${result.errors.length} 个错误`}
                </span>
              </div>

              {result.servers.length > 0 && (
                <div className="mb-4 space-y-2">
                  {result.servers.map((s) => (
                    <div
                      key={s.id}
                      className="flex items-center gap-3 rounded-xl px-3 py-2"
                      style={{
                        backgroundColor: "var(--surface-subtle)",
                        border: "1px solid var(--glass-border)",
                      }}
                    >
                      <CheckCircle2 size={16} style={{ color: "var(--status-success)" }} />
                      <span className="text-sm font-medium" style={{ color: "var(--text-primary)" }}>
                        {s.name}
                      </span>
                      <span
                        className="rounded px-1.5 py-0.5 text-xs"
                        style={{
                          backgroundColor: "var(--surface-base)",
                          color: "var(--text-secondary)",
                        }}
                      >
                        {s.transport.toUpperCase()}
                      </span>
                      <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                        {s.status === "connected" ? "已连接" : s.status === "degraded" ? "需关注" : "未启用"}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {result.errors.length > 0 && (
                <div className="space-y-1">
                  {result.errors.map((err, i) => (
                    <p key={i} className="flex items-start gap-1.5 text-xs" style={{ color: "var(--status-danger)" }}>
                      <AlertCircle size={14} className="mt-0.5 shrink-0" />
                      {err}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          className="flex items-center justify-end gap-3 px-6 py-4"
          style={{ borderTop: "1px solid var(--glass-border)" }}
        >
          <button
            type="button"
            onClick={handleClose}
            className="glass rounded-xl px-4 py-2.5 text-sm font-medium transition-colors"
            style={{ color: "var(--text-secondary)" }}
          >
            {result ? "关闭" : "取消"}
          </button>
          {!result && (
            <button
              type="button"
              onClick={handleImport}
              className="btn-primary inline-flex items-center gap-2"
              disabled={!jsonText.trim() || !!jsonError || importing}
              style={{ opacity: !jsonText.trim() || !!jsonError || importing ? 0.5 : 1 }}
            >
              {importing && <Loader2 size={16} className="animate-spin" />}
              导入并探测
            </button>
          )}
        </div>
      </div>
    </div>,
    document.body,
  );
};

export default JsonImportDialog;
