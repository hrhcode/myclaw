import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { Highlight, themes, Prism } from 'prism-react-renderer';
import type { Language } from 'prism-react-renderer';
import { useTheme } from '../../contexts/ThemeContext';

// Languages already built into prism-react-renderer: c, cpp, css, go, html, javascript, json,
// jsx, markdown, python, rust, sql, tsx, typescript, yaml, bash.
// Extra languages need their grammars loaded and injected into the Prism instance
// that prism-react-renderer uses internally.
const extraLanguages: Record<string, () => Promise<unknown>> = {
  java: () => import('prismjs/components/prism-java'),
  csharp: () => import('prismjs/components/prism-csharp'),
  scss: () => import('prismjs/components/prism-scss'),
  dockerfile: () => import('prismjs/components/prism-docker'),
  makefile: () => import('prismjs/components/prism-makefile'),
  git: () => import('prismjs/components/prism-git'),
};

interface CodeBlockProps {
  language?: string;
  value: string;
}

const loadingLanguages = new Set<string>();

// prismjs component files are IIFEs that register onto the global Prism.
// We temporarily point globalThis.Prism to the bundled Prism so the
// grammars land on the correct instance.
const loadExtraLanguage = async (lang: string) => {
  if (loadingLanguages.has(lang)) return;
  loadingLanguages.add(lang);

  const prev = (globalThis as Record<string, unknown>).Prism;
  (globalThis as Record<string, unknown>).Prism = Prism;

  try {
    await extraLanguages[lang]();
  } finally {
    if (prev === undefined) {
      delete (globalThis as Record<string, unknown>).Prism;
    } else {
      (globalThis as Record<string, unknown>).Prism = prev;
    }
  }
};

const CodeBlock: React.FC<CodeBlockProps> = ({ language = 'code', value }) => {
  const [copied, setCopied] = useState(false);
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const normalizeLanguage = (lang: string): string => {
    const aliases: Record<string, string> = {
      sh: 'bash',
      shell: 'bash',
      zsh: 'bash',
      py: 'python',
      js: 'javascript',
      ts: 'typescript',
      rb: 'ruby',
      cs: 'csharp',
      md: 'markdown',
    };
    return aliases[lang] || lang;
  };

  const resolvedLang = normalizeLanguage(language);

  // Fire-and-forget: load grammar onto the bundled Prism if not yet available.
  if (extraLanguages[resolvedLang] && !Prism.languages[resolvedLang]) {
    loadExtraLanguage(resolvedLang);
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('复制代码失败:', error);
    }
  };

  // Check if the language is supported; fall back to plain text if not.
  const grammar = Prism.languages[resolvedLang];
  const effectiveLang = grammar ? resolvedLang : 'plain';

  return (
    <Highlight theme={isDark ? themes.oneDark : themes.github} code={value} language={effectiveLang as Language}>
      {({ className, style, tokens, getLineProps, getTokenProps }) => (
        <div className="code-block-container">
          <div className="code-header">
            <span className="language-label">{language}</span>
            <button onClick={handleCopy} className="copy-button" title={copied ? '已复制' : '复制代码'}>
              {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
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
