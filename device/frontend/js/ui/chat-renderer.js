/**
 * Module de rendu des bulles de conversation et des Défis Express du Bac (Liquid Glass & SVG Icons).
 */

import { CURRICULUM_DATA } from '../config/curriculum.js';

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

  renderInitialWelcome(onSelectClass, onChallengeClick) {
    const div = document.createElement('div');
    div.className = 'flex items-start gap-3 mb-6 animate-fade-in';
    div.innerHTML = `
      <div class="w-9 h-9 rounded-full overflow-hidden border border-cyan-400/50 flex items-center justify-center shrink-0 shadow-lg shadow-cyan-950/40 bg-slate-900">
        <img src="assets/avatar.png" alt="ALTA" class="w-full h-full object-cover">
      </div>
      <div class="liquid-glass-card p-5 max-w-[96%] flex-1 border border-white/12 shadow-2xl">
        
        <!-- Header Holographique -->
        <div class="flex items-center justify-between mb-4 pb-2.5 border-b border-white/8">
          <div class="text-xs font-bold text-cyan-300 tracking-wide uppercase flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_10px_#10B981]"></span>
            <span>ALTA • Tuteur Pédagogique Intelligent</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="glass-status-badge text-[11px] text-cyan-300 font-mono">Programme Officiel Malien</span>
            <span class="glass-status-badge text-[11px] text-emerald-300 font-mono">100% Hors-Ligne</span>
          </div>
        </div>

        <div class="ai-body-content space-y-4">
          <p class="text-sm md:text-base text-slate-200 leading-relaxed font-sans">
            Bienvenue sur le dispositif Alternia ! Choisis ton niveau pour adapter les démonstrations, formules et exercices à ton programme scolaire :
          </p>

          <!-- Sélecteur de Classes 3D Stylisé -->
          <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <button class="btn-select-class-welcome p-3.5 text-left flex flex-col items-start gap-1.5 rounded-xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/40 to-slate-900/60 hover:border-emerald-400 hover:shadow-[0_0_20px_rgba(16,185,129,0.3)] transition-all transform hover:-translate-y-1" data-class="10eme">
              <div class="flex items-center justify-between w-full">
                <span class="text-sm font-bold text-white tracking-wide">10ème Année</span>
                <span class="hardware-btn-pill text-emerald-400 border-emerald-500/40 bg-emerald-950/50">Touche 1</span>
              </div>
              <span class="text-[11px] text-slate-300 font-normal">Tronc Commun Général & Technique</span>
            </button>

            <button class="btn-select-class-welcome p-3.5 text-left flex flex-col items-start gap-1.5 rounded-xl border border-cyan-500/30 bg-gradient-to-br from-cyan-950/40 to-slate-900/60 hover:border-cyan-400 hover:shadow-[0_0_20px_rgba(2,132,199,0.3)] transition-all transform hover:-translate-y-1" data-class="11eme">
              <div class="flex items-center justify-between w-full">
                <span class="text-sm font-bold text-white tracking-wide">11ème Année</span>
                <span class="hardware-btn-pill text-cyan-400 border-cyan-500/40 bg-cyan-950/50">Touche 2</span>
              </div>
              <span class="text-[11px] text-slate-300 font-normal">Sciences (11S), Lettres (11L), Éco (11SECO)</span>
            </button>

            <button class="btn-select-class-welcome p-3.5 text-left flex flex-col items-start gap-1.5 rounded-xl border border-orange-500/30 bg-gradient-to-br from-orange-950/40 to-slate-900/60 hover:border-orange-400 hover:shadow-[0_0_20px_rgba(241,133,31,0.3)] transition-all transform hover:-translate-y-1" data-class="12eme">
              <div class="flex items-center justify-between w-full">
                <span class="text-sm font-bold text-white tracking-wide">12ème (Terminale)</span>
                <span class="hardware-btn-pill text-[#F1851F] border-orange-500/40 bg-orange-950/50">Touche 3</span>
              </div>
              <span class="text-[11px] text-slate-300 font-normal">Baccalauréat (TSE, TSExp, TSEco, TSS, TLL)</span>
            </button>
          </div>

          <!-- Section Défis Express Tape-à-l'œil (Missions Flash) -->
          <div class="pt-3 border-t border-white/8">
            <div class="flex items-center justify-between mb-2.5">
              <h4 class="text-xs font-bold uppercase tracking-wider text-amber-300 flex items-center gap-1.5 font-mono">
                <svg class="w-3.5 h-3.5 text-amber-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
                <span>Défis Express & Notions Incontournables du Bac :</span>
              </h4>
              <span class="text-[10px] text-slate-400 font-mono">Touche ou clique pour lancer</span>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              
              <div class="challenge-card-glow btn-challenge-trigger" data-query="Donne la formule de De Moivre pour les nombres complexes et montre comment calculer cos(3x)." data-class="12eme">
                <div class="flex items-center justify-between mb-1.5">
                  <span class="badge-challenge-pill badge-challenge-orange">Objectif Bac TSE</span>
                  <span class="text-[10px] text-slate-400 font-mono">Maths</span>
                </div>
                <div class="font-bold text-white text-xs tracking-tight">Formule de Moivre</div>
                <p class="text-[11px] text-slate-300 mt-1 line-clamp-2">Puissances n & trigonométrie complexe des épreuves du Bac.</p>
              </div>

              <div class="challenge-card-glow btn-challenge-trigger" data-query="Énonce la 2ème loi de Newton et explique l'équation du mouvement pour un solide en chute libre." data-class="12eme">
                <div class="flex items-center justify-between mb-1.5">
                  <span class="badge-challenge-pill badge-challenge-cyan">Grand Classique</span>
                  <span class="text-[10px] text-slate-400 font-mono">Physique</span>
                </div>
                <div class="font-bold text-white text-xs tracking-tight">Lois de Newton (F = m.a)</div>
                <p class="text-[11px] text-slate-300 mt-1 line-clamp-2">Dynamique, chute libre et vecteurs accélération.</p>
              </div>

              <div class="challenge-card-glow btn-challenge-trigger" data-query="C'est quoi la photosynthèse de façon simple ? Donne l'équation bilan et les deux phases." data-class="11eme">
                <div class="flex items-center justify-between mb-1.5">
                  <span class="badge-challenge-pill badge-challenge-emerald">Défi SVT</span>
                  <span class="text-[10px] text-slate-400 font-mono">Biologie</span>
                </div>
                <div class="font-bold text-white text-xs tracking-tight">Photosynthèse & Énergie</div>
                <p class="text-[11px] text-slate-300 mt-1 line-clamp-2">Cycle de Calvin, équation bilan et phase photochimique.</p>
              </div>

            </div>
          </div>

          <!-- Indication Touches Physiques -->
          <div class="flex items-center gap-2 text-xs text-slate-400 pt-2 border-t border-white/5 font-mono">
            <svg class="w-4 h-4 text-cyan-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
            <span>Touches boîtier : [1] 10ème, [2] 11ème, [3] 12ème, [4] Parler au micro.</span>
          </div>

        </div>
      </div>
    `;

    // Clic sur sélection de classe
    div.querySelectorAll('.btn-select-class-welcome').forEach(btn => {
      btn.onclick = () => {
        const clsId = btn.getAttribute('data-class');
        if (onSelectClass) onSelectClass(clsId);
      };
    });

    // Clic sur un défi express
    div.querySelectorAll('.btn-challenge-trigger').forEach(card => {
      card.onclick = () => {
        const query = card.getAttribute('data-query');
        const clsId = card.getAttribute('data-class');
        if (onChallengeClick) onChallengeClick(query, clsId);
      };
    });

    this.listContainer.appendChild(div);
    this.scrollToBottom();
  }

  clear() {
    this.listContainer.innerHTML = '';
  }
}
