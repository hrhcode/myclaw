import { useState, useEffect } from 'react';
import { Copy, Check } from 'lucide-react';
import { Highlight, themes, Prism } from 'prism-react-renderer';
import type { Language } from 'prism-react-renderer';
import { useTheme } from '../../contexts/ThemeContext';

const loadLanguages = async () => {
  if (typeof globalThis !== 'undefined') {
    (globalThis as Record<string, unknown>).Prism = Prism;
  }

  const languages = [
    'javascript',
    'typescript',
    'jsx',
    'tsx',
    'python',
    'java',
    'c',
    'cpp',
    'csharp',
    'go',
    'rust',
    'sql',
    'json',
    'yaml',
    'markdown',
    'bash',
    'css',
    'scss',
    'html',
    'xml',
    'makefile',
    'dockerfile',
    'git',
  ];

  for (const lang of languages) {
    try {
      await import(/* @vite-ignore */ `prismjs/components/prism-${lang}`);
    } catch (error) {
      console.warn(`Failed to load prism language: ${lang}`, error);
    }
  }
};

interface CodeBlockProps {
  language?: string;
  value: string;
}

const CodeBlock: React.FC<CodeBlockProps> = ({ language = 'code', value }) => {
  const [copied, setCopied] = useState(false);
  const [languagesLoaded, setLanguagesLoaded] = useState(false);
  const { theme } = useTheme();
  const isDark = theme === 'dark';

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
    } catch (error) {
      console.error('复制代码失败:', error);
    }
  };

  return (
    <Highlight theme={isDark ? themes.oneDark : themes.github} code={value} language={language as Language}>
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
