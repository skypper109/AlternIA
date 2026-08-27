/**
 * Module d'extraction, de rendu KaTeX et de zoom modal des formules scientifiques.
 */

export class KaTeXRenderer {
  constructor({ formulaModalId = 'formula-modal' } = {}) {
    this.formulaModal = document.getElementById(formulaModalId);
    this.modalMath = document.getElementById('formula-modal-math');
    this.modalVars = document.getElementById('formula-modal-vars');
    this.modalSource = document.getElementById('formula-modal-source');
  }

  renderFormulasInElement(element) {
    if (!element) return;
    if (window.renderMathInElement) {
      try {
        window.renderMathInElement(element, {
          delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '\\[', right: '\\]', display: true },
            { left: '$', right: '$', display: false },
            { left: '\\(', right: '\\)', display: false }
          ],
          throwOnError: false
        });
        return;
      } catch (e) {
        console.warn("renderMathInElement error:", e);
      }
    }

    // Fallback direct regex avec katex.renderToString
    if (window.katex) {
      try {
        let html = element.innerHTML;
        // Display math: \[ ... \] ou $$ ... $$
        html = html.replace(/\\\[([\s\S]*?)\\\]|\$\$([\s\S]*?)\$\$/g, (match, p1, p2) => {
          const formula = p1 || p2;
          try {
            return `<div class="my-2 flex justify-center">${window.katex.renderToString(formula.trim(), { displayMode: true, throwOnError: false })}</div>`;
          } catch (e) {
            return match;
          }
        });
        // Inline math: \( ... \) ou $ ... $
        html = html.replace(/\\\(([\s\S]*?)\\\)|\$([^\$\n]+)\$/g, (match, p1, p2) => {
          const formula = p1 || p2;
          try {
            return `<span class="inline-math mx-1">${window.katex.renderToString(formula.trim(), { displayMode: false, throwOnError: false })}</span>`;
          } catch (e) {
            return match;
          }
        });
        element.innerHTML = html;
      } catch (e) {
        console.warn("KaTeX fallback rendering error:", e);
      }
    }
  }

  extractFormula(text) {
    if (!text) return null;
    const displayMathRegex = /\$\$([\s\S]*?)\$\$|\\\[([\s\S]*?)\\\]/;
    const inlineMathRegex = /\$([^\$]+)\$|\\\((.*?)\\\)/;

    let mathMatch = text.match(displayMathRegex);
    if (mathMatch) {
      return (mathMatch[1] || mathMatch[2]).trim();
    }

    const inlineMatch = text.match(inlineMathRegex);
    if (inlineMatch && (inlineMatch[1] || inlineMatch[2]).length > 4) {
      return (inlineMatch[1] || inlineMatch[2]).trim();
    }

    return null;
  }

  renderFormulaCard(formulaLaTeX, variables = [], sourceDoc = null) {
    const card = document.createElement('div');
    card.className = 'formula-spotlight-card animate-fade-in';

    let varsHtml = '';
    if (variables && variables.length > 0) {
      varsHtml = `
        <div class="formula-variables-grid">
          ${variables.map(v => `<div class="variable-chip"><strong>${v.name}</strong>: <span>${v.desc}</span></div>`).join('')}
        </div>
      `;
    }

    card.innerHTML = `
      <div class="flex items-center justify-between mb-2">
        <div class="formula-badge">
          <span>⚡ Formule Pédagogique Clé</span>
        </div>
        <button class="touch-btn text-xs bg-cyan-900/40 hover:bg-cyan-800/60 text-cyan-300 px-2.5 py-1 rounded-lg border border-cyan-500/30 flex items-center gap-1 btn-zoom-formula">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path></svg>
          <span>Plein Écran</span>
        </button>
      </div>

      <div class="formula-math-display" id="math-target-${Date.now()}"></div>
      ${varsHtml}
      ${sourceDoc ? `<div class="text-[11px] text-slate-400 mt-2 flex items-center gap-1"><span>📖 Source :</span> <span class="text-cyan-400 font-medium">${sourceDoc}</span></div>` : ''}
    `;

    const mathTarget = card.querySelector('.formula-math-display');
    try {
      if (window.katex) {
        window.katex.render(formulaLaTeX, mathTarget, {
          displayMode: true,
          throwOnError: false
        });
      } else {
        mathTarget.textContent = formulaLaTeX;
      }
    } catch (e) {
      mathTarget.textContent = formulaLaTeX;
    }

    const zoomBtn = card.querySelector('.btn-zoom-formula');
    if (zoomBtn) {
      zoomBtn.onclick = () => this.openFormulaModal(formulaLaTeX, variables, sourceDoc);
    }

    return card;
  }

  openFormulaModal(formulaLaTeX, variables, sourceDoc) {
    if (!this.formulaModal) return;

    if (window.katex && this.modalMath) {
      window.katex.render(formulaLaTeX, this.modalMath, { displayMode: true, throwOnError: false });
    } else if (this.modalMath) {
      this.modalMath.textContent = formulaLaTeX;
    }

    if (this.modalVars) {
      this.modalVars.innerHTML = variables && variables.length > 0
        ? variables.map(v => `<div class="variable-chip text-sm p-2"><strong>${v.name}</strong> : ${v.desc}</div>`).join('')
        : '';
    }

    if (this.modalSource && sourceDoc) {
      this.modalSource.textContent = `Document officiel : ${sourceDoc}`;
    }

    this.formulaModal.classList.remove('hidden');
  }

  closeFormulaModal() {
    if (this.formulaModal) {
      this.formulaModal.classList.add('hidden');
    }
  }
}
