import { useState, useEffect } from "react";
import { Copy, Check } from "lucide-react";
import { Highlight, themes, Prism } from "prism-react-renderer";
import type { Language } from "prism-react-renderer";
import { useTheme } from "../../contexts/ThemeContext";

/**
 * 动态加载 Prism 语言包
 * 将 Prism 实例挂载到全局对象以支持语言扩展
 */
const loadLanguages = async () => {
  if (typeof globalThis !== "undefined") {
    (globalThis as Record<string, unknown>).Prism = Prism;
  }

  // 按需加载常用语言（使用正确的 prismjs 包名）
  const languages = [
    "javascript",
    "typescript",
    "jsx",
    "tsx",
    "python",
    "java",
    "c",
    "cpp",
    "csharp",
    "go",
    "rust",
    "sql",
    "json",
    "yaml",
    "markdown",
    "bash",
    "css",
    "scss",
    "html",
    "xml",
    "makefile",
    "dockerfile",
    "git",
  ];

  for (const lang of languages) {
    try {
      // @vite-ignore - Vite 无法静态分析此动态 import
      await import(/* @vite-ignore */ `prismjs/components/prism-${lang}`);
    } catch (e) {
      console.warn(`Failed to load prism language: ${lang}`, e);
    }
  }
};

interface CodeBlockProps {
  language?: string;
  value: string;
}

/**
 * 代码块组件 - 带语法高亮、复制按钮和语言标识
 * 使用 prism-react-renderer 实现语法高亮
 */
const CodeBlock: React.FC<CodeBlockProps> = ({ language = "code", value }) => {
  const [copied, setCopied] = useState(false);
  const [languagesLoaded, setLanguagesLoaded] = useState(false);
  const { theme } = useTheme();
  const isDark = theme === "dark";

  useEffect(() => {
    if (!languagesLoaded) {
      loadLanguages().then(() => {
        setLanguagesLoaded(true);
      });
    }
  }, [languagesLoaded]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("复制失败:", err);
    }
  };

  return (
    <Highlight
      theme={isDark ? themes.oneDark : themes.github}
      code={value}
      language={language as Language}
    >
      {({ className, style, tokens, getLineProps, getTokenProps }) => (
        <div className="code-block-container">
          <div className="code-header">
            <span className="language-label">{language}</span>
            <button
              onClick={handleCopy}
              className="copy-button"
              title={copied ? "已复制" : "复制代码"}
            >
              {copied ? (
                <Check size={14} className="text-green-400" />
              ) : (
                <Copy size={14} className="text-gray-400 hover:text-white" />
              )}
            </button>
          </div>
          <pre className={`${className} code-block-pre`} style={style}>
            <code>
              {tokens.map((line, i) => (
                <div {...getLineProps({ line })} key={i} className="code-line">
                  {line.map((token, key) => (
                    <span {...getTokenProps({ token })} key={key} />
                  ))}
                </div>
              ))}
            </code>
          </pre>
        </div>
      )}
    </Highlight>
  );
};

export default CodeBlock;
