(function () {
  'use strict';
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  var CSRF = ($('meta[name="csrf-token"]') || {}).content || '';

  /* ---------- header ---------- */
  var header = $('#header');
  var onScroll = function () { header.classList.toggle('is-scrolled', window.scrollY > 40); };
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  var burger = $('#burger'), nav = $('#nav');
  if (burger) burger.addEventListener('click', function () {
    var open = !nav.classList.contains('is-open');
    nav.classList.toggle('is-open', open);
    burger.setAttribute('aria-expanded', open);
    header.classList.toggle('menu-open', open);
    document.body.classList.toggle('is-locked', open);
  });

  /* ---------- reveal on scroll ---------- */
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    $$('.reveal').forEach(function (el) { io.observe(el); });
  } else {
    $$('.reveal').forEach(function (el) { el.classList.add('is-in'); });
  }

  /* ---------- counters ---------- */
  $$('[data-count]').forEach(function (el) {
    var m = el.dataset.count.match(/^(\d+)(.*)$/);
    if (!m || !('IntersectionObserver' in window)) return;
    var target = +m[1], suffix = m[2];
    var obs = new IntersectionObserver(function (es) {
      if (!es[0].isIntersecting) return;
      obs.disconnect();
      var t0 = performance.now(), dur = 1400;
      (function tick(t) {
        var p = Math.min(1, (t - t0) / dur), v = Math.round(target * (1 - Math.pow(1 - p, 3)));
        el.textContent = v + suffix;
        if (p < 1) requestAnimationFrame(tick);
      })(t0);
    }, { threshold: 0.6 });
    obs.observe(el);
  });

  /* ---------- modal / lightbox helpers ---------- */
  var lastFocus = null;
  function openLayer(el) {
    lastFocus = document.activeElement;
    el.classList.add('is-open');
    el.setAttribute('aria-hidden', 'false');
    document.body.classList.add('is-locked');
    var f = el.querySelector('input:not([type=hidden]):not(.hp), button');
    if (f) setTimeout(function () { f.focus({ preventScroll: true }); }, 60);
  }
  function closeLayer(el) {
    el.classList.remove('is-open');
    el.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('is-locked');
    if (lastFocus) lastFocus.focus({ preventScroll: true });
  }
  $$('.modal, .lightbox').forEach(function (el) {
    el.addEventListener('click', function (e) { if (e.target.closest('[data-close]')) closeLayer(el); });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') $$('.modal.is-open, .lightbox.is-open').forEach(closeLayer);
  });

  /* ---------- lead modal: любые кнопки с data-lead ---------- */
  var modal = $('#lead-modal');
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-lead]');
    if (!btn || !modal) return;
    e.preventDefault();
    var openLb = $('.lightbox.is-open');
    if (openLb) closeLayer(openLb);
    var form = $('form', modal), box = $('.modal__body', modal);
    box.classList.remove('is-sent');
    resetForm(form);
    form.elements.kind.value = btn.dataset.lead || 'consult';
    form.elements.service.value = btn.dataset.service || '';
    form.elements.source.value = btn.dataset.source || document.title;
    $('#lead-modal-title').textContent = btn.dataset.title || 'Оставить заявку';
    $('#lead-modal-eyebrow').textContent = btn.dataset.service ? 'услуга' : 'заявка';
    openLayer(modal);
  });

  /* ---------- project lightbox ---------- */
  var lb = $('#project-lightbox');
  if (lb) {
    document.addEventListener('click', function (e) {
      var card = e.target.closest('[data-project]');
      if (!card) return;
      var p = JSON.parse(card.dataset.project);
      $('.lightbox__img', lb).src = p.img;
      $('.lightbox__img', lb).alt = p.title;
      $('.lightbox__title', lb).textContent = p.title;
      $('.lightbox__kind', lb).textContent = (p.kind || '').toLowerCase();
      $('.lightbox__city', lb).textContent = p.city;
      $('.lightbox__area', lb).textContent = p.area + ' м²';
      $('.lightbox__year', lb).textContent = p.year;
      openLayer(lb);
    });
  }

  /* ---------- «посмотреть ещё» на странице галереи ---------- */
  var more = $('#more-projects');
  if (more) {
    var cards = $$('.gallery-hero .project');
    var step = 6, shown = step;
    cards.forEach(function (c, i) { if (i >= shown) c.classList.add('is-hidden'); });
    if (cards.length <= shown) more.parentNode.hidden = true;
    more.addEventListener('click', function () {
      shown += step;
      cards.forEach(function (c, i) { if (i < shown && c.classList.contains('is-hidden')) { c.classList.remove('is-hidden'); c.classList.add('is-in'); } });
      if (shown >= cards.length) more.parentNode.hidden = true;
    });
  }

  /* ---------- stages: ДИЗАЙН / РЕМОНТ ---------- */
  $$('[data-stages]').forEach(function (root) {
    var tabs = $$('.stages__tab', root), panels = $$('[data-panel]', root), idx = 0;
    function show(i) {
      idx = (i + tabs.length) % tabs.length;
      tabs.forEach(function (t, k) { t.classList.toggle('is-active', k === idx); });
      panels.forEach(function (p) { p.classList.toggle('is-active', p.dataset.panel === tabs[idx].dataset.tab); });
    }
    tabs.forEach(function (t, k) { t.addEventListener('click', function () { show(k); }); });
    $$('.stages__arrow', root).forEach(function (a) { a.addEventListener('click', function () { show(idx + (+a.dataset.dir)); }); });
  });

  /* ---------- slider ---------- */
  $$('[data-slider]').forEach(function (root) {
    var slides = $$('.slider__slide', root), dots = $('.slider__dots', root), i = 0, timer;
    slides.forEach(function (_, k) {
      var d = document.createElement('button');
      d.type = 'button'; d.setAttribute('aria-label', 'Слайд ' + (k + 1));
      d.addEventListener('click', function () { go(k); });
      dots.appendChild(d);
    });
    function go(k) {
      i = (k + slides.length) % slides.length;
      slides.forEach(function (s, n) { s.classList.toggle('is-active', n === i); });
      $$('button', dots).forEach(function (d, n) { d.classList.toggle('is-active', n === i); });
      clearInterval(timer); timer = setInterval(function () { go(i + 1); }, 6000);
    }
    $('.slider__btn--prev', root).addEventListener('click', function () { go(i - 1); });
    $('.slider__btn--next', root).addEventListener('click', function () { go(i + 1); });
    go(0);
  });

  /* ---------- phone mask +7 (___) ___-__-__ ---------- */
  function formatPhone(v) {
    var d = v.replace(/\D/g, '');
    if (!d) return '';
    if (d[0] === '8') d = '7' + d.slice(1);
    if (d[0] !== '7') d = '7' + d;
    d = d.slice(0, 11);
    var out = '+7';
    if (d.length > 1) out += ' (' + d.slice(1, 4);
    if (d.length >= 4) out += ')';
    if (d.length > 4) out += ' ' + d.slice(4, 7);
    if (d.length > 7) out += '-' + d.slice(7, 9);
    if (d.length > 9) out += '-' + d.slice(9, 11);
    return out;
  }
  document.addEventListener('input', function (e) {
    if (e.target.classList && e.target.classList.contains('js-phone')) e.target.value = formatPhone(e.target.value);
    if (e.target.tagName === 'SELECT') e.target.classList.toggle('has-value', !!e.target.value);
    clearFieldError(e.target);
  });
  document.addEventListener('change', function (e) {
    if (e.target.tagName === 'SELECT') e.target.classList.toggle('has-value', !!e.target.value);
    clearFieldError(e.target);
  });
  function clearFieldError(input) {
    var wrap = input.closest && input.closest('.is-invalid');
    if (!wrap) return;
    wrap.classList.remove('is-invalid');
    var em = wrap.querySelector('.field__err');
    if (em) em.textContent = '';
  }

  /* ---------- AJAX-отправка форм ---------- */
  function setError(form, name, msg) {
    var input = form.elements[name];
    if (!input) return;
    var wrap = input.closest('.field, .check');
    if (!wrap) return;
    wrap.classList.toggle('is-invalid', !!msg);
    var em = $('.field__err', wrap);
    if (em) em.textContent = msg || '';
  }
  function resetForm(form) {
    form.reset();
    $$('.is-invalid', form).forEach(function (w) { w.classList.remove('is-invalid'); });
    $$('.field__err', form).forEach(function (em) { em.textContent = ''; });
    $('.form__msg', form).textContent = '';
    $$('select', form).forEach(function (s) { s.classList.remove('has-value'); });
  }
  function validate(form) {
    var ok = true, el = form.elements;
    ['name', 'phone', 'consent', 'email'].forEach(function (n) { setError(form, n, ''); });
    if (!el.name.value.trim() || el.name.value.trim().length < 2) { setError(form, 'name', 'Укажите имя'); ok = false; }
    if (el.phone.value.replace(/\D/g, '').length < 11) { setError(form, 'phone', 'Укажите телефон полностью'); ok = false; }
    if (el.email && el.email.value && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(el.email.value)) { setError(form, 'email', 'Проверьте email'); ok = false; }
    if (!el.consent.checked) { setError(form, 'consent', 'Нужно согласие на обработку данных'); ok = false; }
    return ok;
  }

  $$('.js-form').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var msg = $('.form__msg', form);
      msg.textContent = '';
      if (!validate(form)) return;
      var data = {};
      new FormData(form).forEach(function (v, k) { data[k] = v; });
      var btn = $('button[type=submit]', form), label = $('span', btn), text = label.textContent;
      btn.disabled = true; label.textContent = 'ОТПРАВЛЯЕМ…';
      fetch(form.getAttribute('action'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': CSRF },
        body: JSON.stringify(data)
      })
        .then(function (r) { return r.json().catch(function () { return {}; }); })
        .then(function (res) {
          if (res.ok) {
            form.parentNode.classList.add('is-sent');
            resetForm(form);
            var ok = $('.form-success', form.parentNode);
            if (ok && !form.closest('.modal')) {
              var top = ok.getBoundingClientRect().top;
              if (top < 80 || top > innerHeight - 120) window.scrollTo({ top: top + scrollY - 200, behavior: 'smooth' });
            }
          } else {
            if (res.errors) Object.keys(res.errors).forEach(function (k) { setError(form, k, res.errors[k]); });
            msg.textContent = res.message || (res.errors ? '' : 'Не удалось отправить. Попробуйте ещё раз.');
          }
        })
        .catch(function () { msg.textContent = 'Нет соединения. Попробуйте ещё раз или позвоните нам.'; })
        .then(function () { btn.disabled = false; label.textContent = text; });
    });
  });
})();
