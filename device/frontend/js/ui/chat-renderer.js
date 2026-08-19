/**
 * Module de rendu des bulles de conversation et des messages ALTA (Liquid Glass & SVG Icons).
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
      .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="text-slate-200">$1</em>')
      .replace(/`(.*?)`/g, '<code class="bg-slate-900/80 text-cyan-300 px-1.5 py-0.5 rounded font-mono text-xs border border-cyan-500/20">$1</code>')
      .replace(/\n\n/g, '<br/><br/>')
      .replace(/\n/g, '<br/>');
  }

  appendUserMessage(text, className = "") {
    const div = document.createElement('div');
    div.className = 'flex items-start justify-end gap-3 mb-5 animate-fade-in';
    div.innerHTML = `
      <div class="bubble-user-liquid max-w-[85%]">
        <div class="text-[11px] text-cyan-200 font-semibold mb-1 flex items-center justify-end gap-1.5 opacity-90">
          <span>Élève</span>
          <span>•</span>
          <span>${this.escapeHtml(className)}</span>
        </div>
        <p class="text-sm md:text-base leading-relaxed selectable-text font-normal">${this.escapeHtml(text)}</p>
      </div>
      <div class="w-8 h-8 rounded-full bg-cyan-900/50 border border-cyan-400/40 flex items-center justify-center text-cyan-300 font-bold text-xs shrink-0 shadow-sm">
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
      </div>
    `;
    this.listContainer.appendChild(div);
    this.scrollToBottom();
  }

  createStreamingAIMessage(onFollowupClick) {
    const div = document.createElement('div');
    div.className = 'flex items-start gap-3 mb-6 animate-fade-in';
    div.innerHTML = `
      <div class="w-9 h-9 rounded-full overflow-hidden border border-cyan-400/50 flex items-center justify-center shrink-0 shadow-lg shadow-cyan-950/40 bg-slate-900">
        <img src="assets/avatar.png" alt="ALTA" class="w-full h-full object-cover">
      </div>
      <div class="bubble-ai-liquid max-w-[92%] flex-1">
        <div class="flex items-center justify-between mb-2 pb-2 border-b border-white/5">
          <div class="text-xs font-bold text-cyan-300 tracking-wide uppercase flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
            <span>ALTA • Tuteur Pédagogique</span>
          </div>
          <span class="text-[10px] bg-cyan-950/80 text-cyan-300 px-2 py-0.5 rounded font-mono border border-cyan-700/50 stream-badge">Direct</span>
        </div>
        <div class="ai-body-content">
          <div class="text-sm md:text-base text-slate-100 leading-relaxed selectable-text mb-2 font-sans">
            <span class="streaming-text"></span><span class="inline-block w-1.5 h-4 bg-cyan-400 ml-1 animate-pulse typing-cursor"></span>
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
          streamBadge.textContent = payload.source;
          streamBadge.className = "text-[10px] bg-slate-900/80 text-slate-400 px-2 py-0.5 rounded border border-white/10";
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
            <div class="mt-3 pt-3 border-t border-white/5">
              <button class="glass-chip-btn text-xs hover:border-[#F1851F]/40 hover:bg-[#F1851F]/10 text-orange-200 btn-followup">
                <svg class="w-3.5 h-3.5 text-[#F1851F]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                <span class="opacity-80">Question suggérée :</span>
                <span class="font-medium underline">${this.escapeHtml(payload.followup)}</span>
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

    let contentHtml = `<p class="text-sm md:text-base text-slate-100 leading-relaxed selectable-text mb-2 font-sans">${this.formatMarkdown(payload.answer)}</p>`;

    div.innerHTML = `
      <div class="w-9 h-9 rounded-full overflow-hidden border border-cyan-400/50 flex items-center justify-center shrink-0 shadow-lg shadow-cyan-950/40 bg-slate-900">
        <img src="assets/avatar.png" alt="ALTA" class="w-full h-full object-cover">
      </div>
      <div class="bubble-ai-liquid max-w-[92%] flex-1">
        <div class="flex items-center justify-between mb-2 pb-2 border-b border-white/5">
          <div class="text-xs font-bold text-cyan-300 tracking-wide uppercase flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-cyan-400"></span>
            <span>ALTA • Tuteur Pédagogique</span>
          </div>
          ${payload.source ? `<span class="text-[10px] bg-slate-900/80 text-slate-400 px-2 py-0.5 rounded border border-white/10 font-mono">${this.escapeHtml(payload.source)}</span>` : ''}
        </div>
        <div class="ai-body-content">${contentHtml}</div>
        ${payload.followup ? `
          <div class="mt-3 pt-3 border-t border-white/5">
            <button class="glass-chip-btn text-xs hover:border-[#F1851F]/40 hover:bg-[#F1851F]/10 text-orange-200 btn-followup">
              <svg class="w-3.5 h-3.5 text-[#F1851F]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
              <span class="opacity-80">Question suggérée :</span>
              <span class="font-medium underline">${this.escapeHtml(payload.followup)}</span>
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
      <span class="glass-status-badge text-xs text-cyan-300 font-mono">
        <svg class="w-3 h-3 text-cyan-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
        <span>${this.escapeHtml(text)}</span>
      </span>
    `;
    this.listContainer.appendChild(div);
    this.scrollToBottom();
  }

  renderInitialWelcome(onSelectClass) {
    const div = document.createElement('div');
    div.className = 'flex items-start gap-3 mb-6 animate-fade-in';
    div.innerHTML = `
      <div class="w-9 h-9 rounded-full overflow-hidden border border-cyan-400/50 flex items-center justify-center shrink-0 shadow-lg shadow-cyan-950/40 bg-slate-900">
        <img src="assets/avatar.png" alt="ALTA" class="w-full h-full object-cover">
      </div>
      <div class="liquid-glass-card p-5 max-w-[94%] flex-1 border border-white/10 shadow-2xl">
        <div class="flex items-center justify-between mb-3 pb-2 border-b border-white/5">
          <div class="text-xs font-bold text-cyan-300 tracking-wide uppercase flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span>ALTA • Tuteur Pédagogique Intelligent</span>
          </div>
          <span class="glass-status-badge text-[10.5px] text-cyan-300 font-mono">Programme Officiel Malien</span>
        </div>
        <div class="ai-body-content">
          <p class="text-sm md:text-base text-slate-200 leading-relaxed font-sans mb-4">
            Bienvenue sur le dispositif Alternia. Pour adapter les explications, démarches scientifiques et résolutions d'exercices à ton programme scolaire, sélectionne ton niveau :
          </p>
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 my-3">
            <button class="btn-select-class-welcome glass-tab-btn p-4 text-left flex flex-col items-start gap-1 rounded-xl hover:border-emerald-400/50 hover:bg-emerald-950/30 transition-all" data-class="10eme">
              <div class="flex items-center gap-2">
                <span class="hardware-btn-pill text-emerald-400 border-emerald-500/30">1</span>
                <span class="text-sm font-bold text-white">10ème Année</span>
              </div>
              <span class="text-[11px] text-slate-400 font-normal">Tronc Commun Général & Technique</span>
            </button>
            <button class="btn-select-class-welcome glass-tab-btn p-4 text-left flex flex-col items-start gap-1 rounded-xl hover:border-cyan-400/50 hover:bg-cyan-950/30 transition-all" data-class="11eme">
              <div class="flex items-center gap-2">
                <span class="hardware-btn-pill text-cyan-400 border-cyan-500/30">2</span>
                <span class="text-sm font-bold text-white">11ème Année</span>
              </div>
              <span class="text-[11px] text-slate-400 font-normal">Sciences (S), Lettres (L), Économie (SECO)</span>
            </button>
            <button class="btn-select-class-welcome glass-tab-btn p-4 text-left flex flex-col items-start gap-1 rounded-xl hover:border-[#F1851F]/50 hover:bg-orange-950/30 transition-all" data-class="12eme">
              <div class="flex items-center gap-2">
                <span class="hardware-btn-pill text-[#F1851F] border-[#F1851F]/30">3</span>
                <span class="text-sm font-bold text-white">12ème (Terminale)</span>
              </div>
              <span class="text-[11px] text-slate-400 font-normal">Baccalauréat (TSE, TSExp, TSEco, TSS, TLL)</span>
            </button>
          </div>
          <div class="flex items-center gap-2 text-xs text-slate-400 mt-3 pt-2 border-t border-white/5">
            <svg class="w-4 h-4 text-cyan-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
            <span>Tu peux également utiliser les 4 boutons physiques situés sur le boîtier pour changer de classe ou activer le micro.</span>
          </div>
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
