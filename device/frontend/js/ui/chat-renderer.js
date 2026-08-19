/**
 * Module de rendu des bulles de conversation et des messages ALTA.
 */

export class ChatRenderer {
  constructor({ listContainerId = 'chat-messages-list', scrollAreaId = 'chat-scroll-area', katexRenderer } = {}) {
    this.listContainer = document.getElementById(listContainerId);
    this.scrollArea = document.getElementById(scrollAreaId);
    this.katexRenderer = katexRenderer;
  }

  scrollToBottom() {
    if (this.scrollArea) {
      this.scrollArea.scrollTop = this.scrollArea.scrollHeight;
    }
  }

  escapeHtml(unsafe) {
    if (!unsafe) return "";
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  formatMarkdown(text) {
    if (!text) return "";
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code class="bg-slate-800 text-cyan-300 px-1 py-0.5 rounded text-xs">$1</code>')
      .replace(/\n\n/g, '<br/><br/>')
      .replace(/\n/g, '<br/>');
  }

  appendUserMessage(text, className = "") {
    const div = document.createElement('div');
    div.className = 'flex items-start justify-end gap-3 mb-4 animate-fade-in';
    div.innerHTML = `
      <div class="chat-bubble-user max-w-[85%] p-4 text-white">
        <div class="text-xs text-cyan-200 font-semibold mb-1 flex items-center gap-1">
          <span>Élève (${className})</span>
        </div>
        <p class="text-sm md:text-base leading-relaxed selectable-text">${this.escapeHtml(text)}</p>
      </div>
      <div class="w-9 h-9 rounded-full bg-cyan-600/30 border border-cyan-400 flex items-center justify-center text-cyan-300 font-bold text-sm shrink-0">
        É
      </div>
    `;
    this.listContainer.appendChild(div);
    this.scrollToBottom();
  }

  createStreamingAIMessage(onFollowupClick) {
    const div = document.createElement('div');
    div.className = 'flex items-start gap-3 mb-6 animate-fade-in';
    div.innerHTML = `
      <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-700 to-cyan-500 border border-cyan-300 flex items-center justify-center text-white shrink-0 shadow-lg shadow-cyan-900/40">
        <svg class="w-6 h-6" viewBox="0 0 100 100" fill="none">
          <circle cx="50" cy="50" r="45" fill="#0C142B" />
          <path d="M50 15 C75 25 85 50 85 70 C70 60 55 55 45 65 Z" fill="#F1851F"/>
          <path d="M85 70 C75 90 50 90 35 75 C45 60 60 60 65 45 Z" fill="#0284C7"/>
          <path d="M15 60 C15 35 35 20 50 15 C45 30 50 50 65 55 Z" fill="#314999"/>
        </svg>
      </div>
      <div class="chat-bubble-ai max-w-[90%] p-4 text-white flex-1 border border-slate-700/60">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-bold text-cyan-400 tracking-wide uppercase flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
            ALTA — Tuteur Intelligent (Alternia)
          </span>
          <span class="text-[11px] bg-cyan-950/80 text-cyan-300 px-2 py-0.5 rounded border border-cyan-700/50 stream-badge">⚡ En direct</span>
        </div>
        <div class="ai-body-content">
          <div class="text-sm md:text-base text-slate-100 leading-relaxed selectable-text mb-2">
            <span class="streaming-text"></span><span class="typing-cursor"></span>
          </div>
        </div>
        <div class="followup-container"></div>
      </div>
    `;

    this.listContainer.appendChild(div);
    this.scrollToBottom();

    const textSpan = div.querySelector('.streaming-text');
    const cursor = div.querySelector('.typing-cursor');
    const streamBadge = div.querySelector('.stream-badge');
    const bodyContent = div.querySelector('.ai-body-content');
    const followupContainer = div.querySelector('.followup-container');

    return {
      element: div,
      updateText: (fullText) => {
        if (textSpan) textSpan.innerHTML = this.formatMarkdown(fullText);
        this.scrollToBottom();
      },
      finalize: (payload) => {
        if (cursor) cursor.remove();
        if (payload.source && streamBadge) {
          streamBadge.textContent = `📖 ${payload.source}`;
          streamBadge.className = "text-[11px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700";
        } else if (streamBadge) {
          streamBadge.remove();
        }

        if (this.katexRenderer) {
          const formulaLaTeX = this.katexRenderer.extractFormula(payload.answer);
          if (formulaLaTeX) {
            const formulaCard = this.katexRenderer.renderFormulaCard(formulaLaTeX, [], payload.source);
            bodyContent.appendChild(formulaCard);
          }
        }

        if (payload.followup) {
          followupContainer.innerHTML = `
            <div class="mt-3 pt-3 border-t border-slate-800">
              <button class="touch-btn text-xs bg-gradient-to-r from-orange-600/20 to-cyan-600/20 hover:from-orange-600/40 hover:to-cyan-600/40 border border-orange-500/40 text-orange-200 px-3 py-1.5 rounded-full flex items-center gap-1.5 btn-followup">
                <span>💡 Question suggérée :</span>
                <span class="font-medium underline">${payload.followup}</span>
              </button>
            </div>
          `;
          const followupBtn = followupContainer.querySelector('.btn-followup');
          if (followupBtn && onFollowupClick) {
            followupBtn.onclick = () => onFollowupClick(payload.followup);
          }
        }
        this.scrollToBottom();
      }
    };
  }

  appendAIMessage(payload, onFollowupClick) {
    const div = document.createElement('div');
    div.className = 'flex items-start gap-3 mb-6 animate-fade-in';

    let contentHtml = `<p class="text-sm md:text-base text-slate-100 leading-relaxed selectable-text mb-2">${this.formatMarkdown(payload.answer)}</p>`;

    div.innerHTML = `
      <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-700 to-cyan-500 border border-cyan-300 flex items-center justify-center text-white shrink-0 shadow-lg shadow-cyan-900/40">
        <svg class="w-6 h-6" viewBox="0 0 100 100" fill="none">
          <circle cx="50" cy="50" r="45" fill="#0C142B" />
          <path d="M50 15 C75 25 85 50 85 70 C70 60 55 55 45 65 Z" fill="#F1851F"/>
          <path d="M85 70 C75 90 50 90 35 75 C45 60 60 60 65 45 Z" fill="#0284C7"/>
          <path d="M15 60 C15 35 35 20 50 15 C45 30 50 50 65 55 Z" fill="#314999"/>
        </svg>
      </div>
      <div class="chat-bubble-ai max-w-[90%] p-4 text-white flex-1 border border-slate-700/60">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-bold text-cyan-400 tracking-wide uppercase flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-cyan-400"></span>
            ALTA — Tuteur Intelligent (Alternia)
          </span>
          ${payload.source ? `<span class="text-[11px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700">📖 ${payload.source}</span>` : ''}
        </div>
        <div class="ai-body-content">${contentHtml}</div>
        ${payload.followup ? `
          <div class="mt-3 pt-3 border-t border-slate-800">
            <button class="touch-btn text-xs bg-gradient-to-r from-orange-600/20 to-cyan-600/20 hover:from-orange-600/40 hover:to-cyan-600/40 border border-orange-500/40 text-orange-200 px-3 py-1.5 rounded-full flex items-center gap-1.5 btn-followup">
              <span>💡 Question suggérée :</span>
              <span class="font-medium underline">${payload.followup}</span>
            </button>
          </div>
        ` : ''}
      </div>
    `;

    if (payload.formula && this.katexRenderer) {
      const bodyContainer = div.querySelector('.ai-body-content');
      const formulaCard = this.katexRenderer.renderFormulaCard(payload.formula, payload.variables, payload.source);
      bodyContainer.appendChild(formulaCard);
    }

    const followupBtn = div.querySelector('.btn-followup');
    if (followupBtn && payload.followup && onFollowupClick) {
      followupBtn.onclick = () => onFollowupClick(payload.followup);
    }

    this.listContainer.appendChild(div);
    this.scrollToBottom();
  }

  addSystemNotification(text) {
    const div = document.createElement('div');
    div.className = 'text-center my-3 animate-fade-in';
    div.innerHTML = `
      <span class="text-xs bg-slate-800/90 text-cyan-300 border border-cyan-500/30 px-3 py-1 rounded-full shadow">
        ℹ️ ${this.escapeHtml(text)}
      </span>
    `;
    this.listContainer.appendChild(div);
    this.scrollToBottom();
  }

  renderInitialWelcome(onSelectClass) {
    const div = document.createElement('div');
    div.className = 'flex items-start gap-3 mb-6 animate-fade-in';
    div.innerHTML = `
      <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-700 to-cyan-500 border border-cyan-300 flex items-center justify-center text-white shrink-0 shadow-lg shadow-cyan-900/40">
        <svg class="w-6 h-6" viewBox="0 0 100 100" fill="none">
          <circle cx="50" cy="50" r="45" fill="#0C142B" />
          <path d="M50 15 C75 25 85 50 85 70 C70 60 55 55 45 65 Z" fill="#F1851F"/>
          <path d="M85 70 C75 90 50 90 35 75 C45 60 60 60 65 45 Z" fill="#0284C7"/>
          <path d="M15 60 C15 35 35 20 50 15 C45 30 50 50 65 55 Z" fill="#314999"/>
        </svg>
      </div>
      <div class="chat-bubble-ai max-w-[92%] p-5 text-white flex-1 border border-slate-700/60 shadow-xl rounded-2xl bg-slate-900/90">
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-bold text-cyan-400 tracking-wide uppercase flex items-center gap-1.5">
            <span class="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
            ALTA — Tuteur Pédagogique Intelligent (Alternia)
          </span>
          <span class="text-[11px] bg-slate-800 text-cyan-300 px-2.5 py-0.5 rounded-full border border-cyan-500/30">🇲🇱 Programme Officiel Malien</span>
        </div>
        <div class="ai-body-content">
          <p class="text-sm md:text-base text-slate-100 leading-relaxed selectable-text mb-3">
            Bonjour ! Je suis <strong>ALTA</strong>, ton assistant pédagogique personnel. 👋<br>
            Pour que j'adapte mes explications, résolutions et formules scientifiques à ton niveau exact, <strong>choisis ta classe pour commencer</strong> :
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 my-3">
            <button class="btn-select-class-welcome touch-btn p-3.5 rounded-xl border border-emerald-500/40 bg-emerald-950/40 hover:bg-emerald-900/60 text-left transition-all flex flex-col gap-1.5 shadow-md hover:border-emerald-300 hover:scale-[1.02]" data-class="10eme">
              <span class="text-sm font-bold text-emerald-300 flex items-center gap-1.5">📐 10ème Année</span>
              <span class="text-[11px] text-slate-300">Tronc Commun Scientifique & Littéraire</span>
            </button>
            <button class="btn-select-class-welcome touch-btn p-3.5 rounded-xl border border-cyan-500/40 bg-cyan-950/40 hover:bg-cyan-900/60 text-left transition-all flex flex-col gap-1.5 shadow-md hover:border-cyan-300 hover:scale-[1.02]" data-class="11eme">
              <span class="text-sm font-bold text-cyan-300 flex items-center gap-1.5">⚡ 11ème Année</span>
              <span class="text-[11px] text-slate-300">Sciences (S), Lettres (L) ou Économie (SECO)</span>
            </button>
            <button class="btn-select-class-welcome touch-btn p-3.5 rounded-xl border border-purple-500/50 bg-purple-950/40 hover:bg-purple-900/60 text-left transition-all flex flex-col gap-1.5 shadow-md hover:border-purple-400 hover:scale-[1.02]" data-class="12eme">
              <span class="text-sm font-bold text-purple-300 flex items-center gap-1.5">🎓 12ème (Terminale)</span>
              <span class="text-[11px] text-slate-300">Baccalauréat (TSE, TSExp, TSS, TSEco, TLL)</span>
            </button>
          </div>
          <p class="text-xs text-slate-400 italic mt-2">💡 Tu pourras aussi changer de classe et de matière à tout moment en haut de l'écran ou avec les boutons de la Box.</p>
        </div>
      </div>
    `;

    div.querySelectorAll('.btn-select-class-welcome').forEach(btn => {
      btn.onclick = () => {
        const clsId = btn.getAttribute('data-class');
        if (onSelectClass) onSelectClass(clsId);
      };
    });

    this.listContainer.appendChild(div);
    this.scrollToBottom();
  }

  clear() {
    this.listContainer.innerHTML = '';
  }
}
