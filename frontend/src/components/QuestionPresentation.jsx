import React from 'react';
import ReactMarkdown from 'react-markdown';
import {
  FileCode,
  ArrowRightCircle,
  Sparkles,
  Layers,
  Terminal,
  Clock,
  Database,
  Hash,
} from 'lucide-react';

export function normalizeQuestionText(rawText) {
  if (!rawText) return '';

  let text = rawText.trim();

  // Strip accidental prefixes like "Spoken Conceptual Question:" or "**Spoken Conceptual Question:**"
  text = text.replace(/^(?:\*\*)?(?:Spoken Conceptual Question|Conceptual Question|Spoken Question|Interview Question|Question):?(?:\*\*)?\s*/i, '');

  // Ensure double newlines before common interview problem section headers
  text = text
    .replace(/(?:\*\*|__)?(Problem Statement|Problem Description|Task):?(?:\*\*|__)?\s*/gi, '\n\n### 📋 Problem Statement\n\n')
    .replace(/(?:\*\*|__)?(Input Specification|Input Format|Input):?(?:\*\*|__)?\s*/gi, '\n\n### 📥 Input Format\n\n')
    .replace(/(?:\*\*|__)?(Output Specification|Output Format|Output):?(?:\*\*|__)?\s*/gi, '\n\n### 📤 Output Format\n\n')
    .replace(/(?:\*\*|__)?(Constraints|Key Constraints):?(?:\*\*|__)?\s*/gi, '\n\n### ⚡ Constraints\n\n')
    .replace(/(?:\*\*|__)?(Examples?|Sample Test Case):?(?:\*\*|__)?\s*/gi, '\n\n### 💡 Example Test Case\n\n')
    .replace(/(?:\*\*|__)?(Explanation|Sample Explanation):?(?:\*\*|__)?\s*/gi, '\n\n**Explanation:** ');

  // Fix markdown list dashes stuck to previous sentences
  text = text.replace(/([^\n])\s*-\s*`/g, '$1\n- `');
  text = text.replace(/([^\n])\s*-\s*([A-Za-z0-9])/g, '$1\n- $2');

  return text.trim();
}

export default function QuestionPresentation({ questionText, questionType, topicId }) {
  if (!questionText) {
    return (
      <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic', padding: '1rem 0' }}>
        Loading question...
      </div>
    );
  }

  // Strip accidental LLM prefixes from spoken or coding questions
  const cleanRawText = questionText.replace(
    /^(?:\*\*)?(?:Spoken Conceptual Question|Conceptual Question|Spoken Question|Interview Question|Question):?(?:\*\*)?\s*/i,
    ''
  ).trim();

  const isStructuredCoding =
    questionType === 'coding' ||
    cleanRawText.includes('Problem Statement') ||
    cleanRawText.includes('Input Format') ||
    cleanRawText.includes('Constraints') ||
    cleanRawText.includes('Example');

  const isSql =
    questionType === 'coding' &&
    ((topicId && (topicId === 'dbms_sql_queries' || topicId.includes('sql'))) ||
      cleanRawText.toLowerCase().includes('write an sql query') ||
      cleanRawText.toLowerCase().includes('write a query') ||
      cleanRawText.toLowerCase().includes('from the `orders`'));

  const processedText = isStructuredCoding ? normalizeQuestionText(cleanRawText) : cleanRawText;

  // Custom component renderers for rich presentation
  const customRenderers = {
    h3: ({ children }) => {
      const textContent = String(children);
      let badgeColor = 'var(--accent-primary)';
      let bgGrad = 'rgba(99, 102, 241, 0.12)';
      let borderCol = 'rgba(99, 102, 241, 0.3)';

      if (textContent.includes('Constraints')) {
        badgeColor = '#F59E0B';
        bgGrad = 'rgba(245, 158, 11, 0.12)';
        borderCol = 'rgba(245, 158, 11, 0.3)';
      } else if (textContent.includes('Example')) {
        badgeColor = '#10B981';
        bgGrad = 'rgba(16, 185, 129, 0.12)';
        borderCol = 'rgba(16, 185, 129, 0.3)';
      } else if (textContent.includes('Output')) {
        badgeColor = '#06B6D4';
        bgGrad = 'rgba(6, 182, 212, 0.12)';
        borderCol = 'rgba(6, 182, 212, 0.3)';
      }

      return (
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.35rem 0.85rem',
            borderRadius: '8px',
            background: bgGrad,
            border: `1px solid ${borderCol}`,
            color: badgeColor,
            fontSize: '0.95rem',
            fontWeight: 700,
            marginTop: '1.5rem',
            marginBottom: '0.65rem',
            letterSpacing: '0.02em',
          }}
        >
          {children}
        </div>
      );
    },
    p: ({ children }) => (
      <p
        style={{
          fontSize: isStructuredCoding ? '1.02rem' : '1.25rem',
          lineHeight: '1.65',
          color: '#E2E8F0',
          marginBottom: '0.85rem',
          fontWeight: isStructuredCoding ? 400 : 500,
        }}
      >
        {children}
      </p>
    ),
    code: ({ inline, children }) => {
      return (
        <code
          style={{
            background: 'rgba(6, 182, 212, 0.15)',
            color: '#38BDF8',
            padding: '0.15rem 0.45rem',
            borderRadius: '5px',
            fontFamily: 'monospace',
            fontSize: '0.92em',
            fontWeight: 600,
            border: '1px solid rgba(6, 182, 212, 0.25)',
          }}
        >
          {children}
        </code>
      );
    },
    pre: ({ children }) => (
      <div
        style={{
          background: 'rgba(11, 17, 32, 0.85)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '8px',
          padding: '0.85rem 1.25rem',
          margin: '0.75rem 0',
          overflowX: 'auto',
          fontFamily: 'monospace',
          fontSize: '0.9rem',
          color: '#A7F3D0',
          lineHeight: '1.5',
        }}
      >
        <pre style={{ margin: 0 }}>{children}</pre>
      </div>
    ),
    ul: ({ children }) => (
      <ul
        style={{
          margin: '0.5rem 0 1rem 1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.4rem',
          color: 'var(--text-secondary)',
          fontSize: '0.95rem',
          lineHeight: '1.5',
        }}
      >
        {children}
      </ul>
    ),
    li: ({ children }) => (
      <li style={{ color: '#CBD5E1' }}>
        {children}
      </li>
    ),
    strong: ({ children }) => (
      <strong style={{ color: '#FFFFFF', fontWeight: 600 }}>
        {children}
      </strong>
    ),
  };

  return (
    <div className="question-presentation-container">
      {/* Visual Sub-Header Tag */}
      {isSql && (
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', marginBottom: '0.75rem' }}>
          <span className="badge badge-cyan" style={{ fontSize: '0.75rem', padding: '0.2rem 0.6rem' }}>
            <Database size={13} /> Relational Query Challenge
          </span>
        </div>
      )}

      {/* Main Markdown Body */}
      <div style={{ lineHeight: '1.6' }}>
        <ReactMarkdown components={customRenderers}>
          {processedText}
        </ReactMarkdown>
      </div>
    </div>
  );
}
