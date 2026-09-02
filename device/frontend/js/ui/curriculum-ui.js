/**
 * Module de gestion de l'interface des classes, matières et Défis Express du Bac (Lycée Malien).
 * Rendu dynamique, gamifié, tape-à-l'œil et 100% interactif pour les élèves.
 */

import { CURRICULUM_DATA } from '../config/curriculum.js';

export class CurriculumUI {
  constructor({
    classContainerId = 'class-selector-tabs',
    subjectContainerId = 'subject-selector-tabs',
    topicContainerId = 'topic-chips-container',
    activeClassLabelId = 'active-class-label',
    activeSubjectLabelId = 'active-subject-label',
    onClassSelect,
    onSubjectSelect,
    onTopicClick
  } = {}) {
    this.classContainer = document.getElementById(classContainerId);
    this.subjectContainer = document.getElementById(subjectContainerId);
    this.topicContainer = document.getElementById(topicContainerId);
    this.activeClassLabel = document.getElementById(activeClassLabelId);
    this.activeSubjectLabel = document.getElementById(activeSubjectLabelId);

    this.onClassSelect = onClassSelect;
    this.onSubjectSelect = onSubjectSelect;
    this.onTopicClick = onTopicClick;

    this.currentClass = '10eme';
    this.currentSubject = 'mathematiques';
  }

  static getSubjectSvg(type) {
    switch (type) {
      case 'math':
        return `<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="9" x2="20" y2="9"></line><line x1="4" y1="15" x2="20" y2="15"></line><line x1="10" y1="3" x2="8" y2="21"></line><line x1="16" y1="3" x2="14" y2="21"></line></svg>`;
      case 'physics':
        return `<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>`;
      case 'chemistry':
        return `<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2v7.31"></path><path d="M14 9.3V2"></path><path d="M8.5 2h7"></path><path d="M14 9.3a6.5 6.5 0 1 1-4 0"></path><path d="M5.52 16h12.96"></path></svg>`;
      case 'biology':
        return `<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 15c6.667-6 13.333 0 20-6"></path><path d="M9 22c1.798-1.998 2.518-3.995 2.807-5.993"></path><path d="M15 2c-1.798 1.998-2.518 3.995-2.807 5.993"></path><path d="M17 17a5 5 0 0 0-5-5"></path><path d="M7 7a5 5 0 0 0 5 5"></path></svg>`;
      case 'literature':
        return `<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>`;
      case 'history':
        return `<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>`;
      case 'philosophy':
        return `<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 22h16"></path><path d="M4 2h16"></path><path d="M9 2v20"></path><path d="M15 2v20"></path></svg>`;
      case 'languages':
        return `<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="m4.93 4.93 4.24 4.24"></path><path d="m14.83 9.17 4.24-4.24"></path><path d="m14.83 14.83 4.24 4.24"></path><path d="m9.17 14.83-4.24 4.24"></path><circle cx="12" cy="12" r="4"></circle></svg>`;
      default:
        return `<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle></svg>`;
    }
  }

  render(currentClass, currentSubject) {
    this.currentClass = currentClass;
    this.currentSubject = currentSubject;

    this.renderClasses();
    this.renderSubjects();
    this.renderTopics();
    this.updateBadges();
  }

  renderClasses() {
    if (!this.classContainer) return;
    this.classContainer.innerHTML = '';

    CURRICULUM_DATA.classes.forEach(c => {
      const btn = document.createElement('button');
      const isActive = c.id === this.currentClass;
      btn.className = `glass-tab-btn ${isActive ? 'active shadow-lg shadow-cyan-950/50' : ''}`;
      
      const dotColor = c.id === '10eme' ? 'bg-emerald-400' : c.id === '11eme' ? 'bg-cyan-400' : 'bg-orange-400';

      btn.innerHTML = `
        <span class="w-2 h-2 rounded-full ${isActive ? 'bg-white shadow-[0_0_8px_#ffffff]' : dotColor}"></span>
        <span class="tracking-wide">${c.name}</span>
        <span class="text-[10px] px-1.5 py-0.5 rounded bg-white/10 opacity-85 font-mono uppercase font-bold">${c.badge}</span>
      `;
      btn.onclick = () => {
        if (this.onClassSelect) this.onClassSelect(c.id);
      };
      this.classContainer.appendChild(btn);
    });
  }

  renderSubjects() {
    if (!this.subjectContainer) return;
    const classObj = this.getClassObj(this.currentClass);
    this.subjectContainer.innerHTML = '';

    classObj.subjects.forEach(s => {
      const btn = document.createElement('button');
      const isActive = s.id === this.currentSubject;
      btn.className = `glass-tab-btn ${isActive ? 'active' : ''}`;
      btn.innerHTML = `
        <span class="${isActive ? 'text-white' : 'text-cyan-300'} flex items-center">${CurriculumUI.getSubjectSvg(s.iconType)}</span>
        <span>${s.name}</span>
      `;
      btn.onclick = () => {
        if (this.onSubjectSelect) this.onSubjectSelect(s.id);
      };
      this.subjectContainer.appendChild(btn);
    });
  }

  renderTopics() {
    if (!this.topicContainer) return;
    const classObj = this.getClassObj(this.currentClass);
    const rawTopics = (classObj.topics && classObj.topics[this.currentSubject]) || [];

    this.topicContainer.innerHTML = '';

    rawTopics.forEach(item => {
      const topicTitle = typeof item === 'string' ? item : item.title;
      const tagText = typeof item === 'object' && item.tag ? item.tag : 'Notion Clé';
      const tagType = typeof item === 'object' && item.type ? item.type : 'cyan';

      let tagClass = 'badge-challenge-cyan';
      if (tagType === 'orange') tagClass = 'badge-challenge-orange';
      if (tagType === 'emerald') tagClass = 'badge-challenge-emerald';
      if (tagType === 'purple') tagClass = 'badge-challenge-purple';

      const chip = document.createElement('button');
      chip.className = 'glass-chip-btn group hover:border-cyan-400/60 hover:bg-cyan-950/40 transition-all';
      chip.innerHTML = `
        <span class="badge-challenge-pill ${tagClass}">${tagText}</span>
        <span class="text-slate-200 group-hover:text-white font-medium text-xs">${topicTitle}</span>
        <svg class="w-3.5 h-3.5 text-cyan-400 opacity-60 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 3L11 8L6 13"/></svg>
      `;
      chip.onclick = () => {
        if (this.onTopicClick) this.onTopicClick(topicTitle);
      };
      this.topicContainer.appendChild(chip);
    });
  }

  updateBadges() {
    const classObj = this.getClassObj(this.currentClass);
    const subjectObj = this.getSubjectObj(this.currentClass, this.currentSubject);

    if (this.activeClassLabel) {
      this.activeClassLabel.textContent = `${classObj.name} (${classObj.badge})`;
    }
    if (this.activeSubjectLabel) {
      this.activeSubjectLabel.innerHTML = `
        <span class="inline-flex items-center gap-1.5">
          ${CurriculumUI.getSubjectSvg(subjectObj.iconType)}
          <span>${subjectObj.name}</span>
        </span>
      `;
    }
  }

  getClassObj(classId) {
    return CURRICULUM_DATA.classes.find(c => c.id === classId) || CURRICULUM_DATA.classes[0];
  }

  getSubjectObj(classId, subjectId) {
    const classObj = this.getClassObj(classId);
    return classObj.subjects.find(s => s.id === subjectId) || { name: subjectId, iconType: "default" };
  }
}
