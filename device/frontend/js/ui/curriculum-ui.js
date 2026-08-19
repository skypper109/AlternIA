/**
 * Module de gestion de l'interface des classes et matières du Lycée Malien.
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
      btn.className = `pill-tab touch-btn ${c.id === this.currentClass ? 'active' : ''}`;
      btn.textContent = `${c.name} (${c.badge})`;
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
      btn.className = `pill-tab touch-btn ${s.id === this.currentSubject ? 'active' : ''}`;
      btn.innerHTML = `<span>${s.icon}</span> <span>${s.name}</span>`;
      btn.onclick = () => {
        if (this.onSubjectSelect) this.onSubjectSelect(s.id);
      };
      this.subjectContainer.appendChild(btn);
    });
  }

  renderTopics() {
    if (!this.topicContainer) return;
    const classObj = this.getClassObj(this.currentClass);
    const topics = (classObj.topics && classObj.topics[this.currentSubject]) || [
      "Explique-moi ce chapitre",
      "Donne-moi la formule clé",
      "Propose-moi un exercice type Bac",
      "Comment résoudre ce problème ?"
    ];

    this.topicContainer.innerHTML = '';
    topics.forEach(topic => {
      const chip = document.createElement('button');
      chip.className = 'touch-btn text-xs bg-slate-800/80 hover:bg-cyan-950/60 border border-slate-700/60 text-slate-200 px-3 py-1.5 rounded-full transition-all';
      chip.textContent = topic;
      chip.onclick = () => {
        if (this.onTopicClick) this.onTopicClick(topic);
      };
      this.topicContainer.appendChild(chip);
    });
  }

  updateBadges() {
    const classObj = this.getClassObj(this.currentClass);
    const subjectObj = this.getSubjectObj(this.currentClass, this.currentSubject);

    if (this.activeClassLabel) {
      this.activeClassLabel.textContent = `${classObj.name}`;
    }
    if (this.activeSubjectLabel) {
      this.activeSubjectLabel.textContent = `${subjectObj.icon} ${subjectObj.name}`;
    }
  }

  getClassObj(classId) {
    return CURRICULUM_DATA.classes.find(c => c.id === classId) || CURRICULUM_DATA.classes[0];
  }

  getSubjectObj(classId, subjectId) {
    const classObj = this.getClassObj(classId);
    return classObj.subjects.find(s => s.id === subjectId) || { name: subjectId, icon: "📖" };
  }
}
