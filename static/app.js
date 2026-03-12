(function () {
  const API = '';
  function get(url) { return fetch(API + url).then(function (r) { return r.json(); }); }
  function post(url, body) { return fetch(API + url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(function (r) { return r.json(); }); }
  function put(url, body) { return fetch(API + url, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(function (r) { return r.json(); }); }

  function showPage(name) {
    document.querySelectorAll('.page').forEach(function (el) { el.classList.add('hide'); });
    document.querySelectorAll('.sidebar a').forEach(function (a) { a.classList.remove('active'); });
    var page = document.getElementById('page-' + name);
    var link = document.querySelector('[data-page="' + name + '"]');
    if (page) page.classList.remove('hide');
    if (link) link.classList.add('active');
    if (name === 'home') loadStats();
    if (name === 'customers') loadCustomers();
    if (name === 'health') loadHealthPage();
    if (name === 'appointments') loadAppointmentsPage();
    if (name === 'home-appointments') loadHomeAppointmentsPage();
    if (name === 'checkins') loadCheckinsPage();
    if (name === 'usage') loadUsagePage();
    if (name === 'surveys') loadSurveysPage();
  }

  function loadStats() {
    get('/api/dashboard/stats').then(function (data) {
      var html = [
        { num: data.total_customers, label: '客户总数' },
        { num: data.today_appointments, label: '今日预约' },
        { num: data.pending_appointments, label: '待处理预约' },
        { num: data.available_equipment + '/' + data.total_equipment, label: '可用设备' }
      ].map(function (s) { return '<div class="stat-box"><div class="num">' + s.num + '</div><div class="label">' + s.label + '</div></div>'; }).join('');
      document.getElementById('stats').innerHTML = html;
    }).catch(function () {});

    get('/api/dashboard/analytics').then(function (data) {
      renderAppointmentTrend(data.appointment_trend || []);
      renderAppointmentStatus(data.appointment_status || []);
      renderEquipmentUsageTop(data.equipment_usage_top || []);
      renderSatisfactionSummary(data.satisfaction || {}, data.customer_activity || {});
    }).catch(function () {
      document.getElementById('appointment-trend').innerHTML = '<p style="color:#666">暂无数据</p>';
      document.getElementById('appointment-status').innerHTML = '<tr><td colspan="2">暂无数据</td></tr>';
      document.getElementById('equipment-usage-top').innerHTML = '<tr><td colspan="3">暂无数据</td></tr>';
      document.getElementById('satisfaction-summary').innerHTML = '<tr><td>暂无数据</td><td>-</td></tr>';
    });
  }

  function renderAppointmentTrend(list) {
    var box = document.getElementById('appointment-trend');
    if (!box) return;
    if (!list.length) {
      box.innerHTML = '<p style="color:#666">暂无预约数据</p>';
      return;
    }
    var max = Math.max.apply(null, list.map(function (x) { return x.count || 0; }).concat([1]));
    box.innerHTML = list.map(function (x) {
      var pct = Math.round(((x.count || 0) / max) * 100);
      return '<div class="trend-bar"><div class="date">' + x.date + '</div><div class="bar"><span style="width:' + pct + '%"></span></div><div class="value">' + (x.count || 0) + '</div></div>';
    }).join('');
  }

  function renderAppointmentStatus(list) {
    var tbody = document.getElementById('appointment-status');
    if (!tbody) return;
    if (!list.length) {
      tbody.innerHTML = '<tr><td colspan="2">暂无数据</td></tr>';
      return;
    }
    tbody.innerHTML = list.map(function (x) {
      var label = x.status === 'scheduled' ? '已预约' : (x.status === 'cancelled' ? '已取消' : (x.status || '-'));
      return '<tr><td>' + label + '</td><td>' + x.n + '</td></tr>';
    }).join('');
  }

  function renderEquipmentUsageTop(list) {
    var tbody = document.getElementById('equipment-usage-top');
    if (!tbody) return;
    if (!list.length) {
      tbody.innerHTML = '<tr><td colspan="3">暂无数据</td></tr>';
      return;
    }
    tbody.innerHTML = list.map(function (x) {
      return '<tr><td>' + (x.equipment_name || '-') + '</td><td>' + (x.usage_count || 0) + '</td><td>' + (x.total_duration_minutes || 0) + '</td></tr>';
    }).join('');
  }

  function renderSatisfactionSummary(satisfaction, activity) {
    var tbody = document.getElementById('satisfaction-summary');
    if (!tbody) return;
    function n(v) { return v == null ? '-' : v; }
    var rows = [
      ['调查样本数', n(satisfaction.survey_count)],
      ['综合满意度(均分)', n(satisfaction.avg_overall)],
      ['服务评分(均分)', n(satisfaction.avg_service)],
      ['设备评分(均分)', n(satisfaction.avg_equipment)],
      ['环境评分(均分)', n(satisfaction.avg_environment)],
      ['人员评分(均分)', n(satisfaction.avg_staff)],
      ['活跃客户占比', (activity.total_customers ? Math.round((activity.active_customers || 0) * 100 / activity.total_customers) : 0) + '%']
    ];
    tbody.innerHTML = rows.map(function (r) { return '<tr><td>' + r[0] + '</td><td>' + r[1] + '</td></tr>'; }).join('');
  }

  function fillCustomerSelect(selId) {
    get('/api/customers').then(function (list) {
      var sel = document.getElementById(selId);
      if (!sel) return;
      var old = sel.value;
      sel.innerHTML = '<option value="">请选择客户</option>' + (list || []).map(function (c) { return '<option value="' + c.id + '">' + c.name + ' ' + (c.phone || '') + '</option>'; }).join('');
      if (old) sel.value = old;
    });
  }

  function fillEquipmentSelect(selId) {
    get('/api/equipment').then(function (list) {
      var sel = document.getElementById(selId);
      if (!sel) return;
      var old = sel.value;
      sel.innerHTML = '<option value="">请选择设备</option>' + (list || []).map(function (e) { return '<option value="' + e.id + '">' + e.name + '</option>'; }).join('');
      if (old) sel.value = old;
    });
  }

  function fillProjectSelect(selId, enabledOnly) {
    get(enabledOnly ? '/api/projects/enabled' : '/api/projects').then(function (list) {
      var sel = document.getElementById(selId);
      if (!sel) return;
      var old = sel.value;
      sel.innerHTML = '<option value="">请选择项目</option>' + (list || []).map(function (p) { return '<option value="' + p.id + '">' + p.name + '</option>'; }).join('');
      if (old) sel.value = old;
    });
  }

  function fillStaffSelect(selId) {
    get('/api/staff/available').then(function (list) {
      var sel = document.getElementById(selId);
      if (!sel) return;
      var old = sel.value;
      sel.innerHTML = '<option value="">不指定</option>' + (list || []).map(function (s) { return '<option value="' + s.id + '">' + s.name + '</option>'; }).join('');
      if (old) sel.value = old;
    });
  }

  function loadCustomers() {
    var q = document.getElementById('customer-search').value;
    get('/api/customers' + (q ? '?search=' + encodeURIComponent(q) : '')).then(function (list) {
      var tbody = document.getElementById('customer-list');
      tbody.innerHTML = (list || []).map(function (c) {
        return '<tr><td>' + c.name + '</td><td>' + (c.id_card || '') + '</td><td>' + (c.phone || '') + '</td><td><button class="btn btn-small btn-primary" data-edit="' + c.id + '">编辑</button></td></tr>';
      }).join('');
      tbody.querySelectorAll('[data-edit]').forEach(function (btn) {
        btn.addEventListener('click', function () { openCustomerModal(btn.dataset.edit); });
      });
    });
  }

  function showMsg(id, text, isErr) {
    var el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = text ? '<div class="msg ' + (isErr ? 'err' : 'ok') + '">' + text + '</div>' : '';
  }

  function openCustomerModal(id) {
    document.getElementById('modal-customer-id').value = id || '';
    document.getElementById('modal-customer-title').textContent = id ? '编辑客户' : '新增客户';
    if (id) {
      get('/api/customers/' + id).then(function (c) {
        document.getElementById('mc-name').value = c.name || '';
        document.getElementById('mc-id_card').value = c.id_card || '';
        document.getElementById('mc-phone').value = c.phone || '';
        document.getElementById('mc-email').value = c.email || '';
        document.getElementById('mc-address').value = c.address || '';
        document.getElementById('mc-gender').value = c.gender || '';
        document.getElementById('mc-birth_date').value = (c.birth_date || '').slice(0, 10);
        document.getElementById('mc-medical_history').value = c.medical_history || '';
        document.getElementById('mc-allergies').value = c.allergies || '';
        document.getElementById('mc-diet_habits').value = c.diet_habits || '';
        document.getElementById('mc-chronic_diseases').value = c.chronic_diseases || '';
        document.getElementById('mc-health_status').value = c.health_status || '';
        document.getElementById('mc-therapy_contraindications').value = c.therapy_contraindications || '';
      });
    } else {
      ['mc-name', 'mc-id_card', 'mc-phone', 'mc-email', 'mc-address', 'mc-gender', 'mc-birth_date', 'mc-medical_history', 'mc-allergies', 'mc-diet_habits', 'mc-chronic_diseases', 'mc-health_status', 'mc-therapy_contraindications'].forEach(function (k) {
        var e = document.getElementById(k);
        if (e) e.value = e.tagName === 'SELECT' ? '' : '';
      });
    }
    document.getElementById('modal-customer').classList.remove('hide');
  }

  function healthValue() {
    var ids = Array.prototype.slice.call(arguments);
    for (var i = 0; i < ids.length; i += 1) {
      var el = document.getElementById(ids[i]);
      if (el) return el.value || null;
    }
    return null;
  }

  function loadHealthPage() {
    fillCustomerSelect('health-customer');
    get('/api/health-assessments').then(function (list) {
      var tbody = document.getElementById('health-list');
      tbody.innerHTML = (list || []).map(function (h) {
        return '<tr><td>' + (h.customer_name || '') + '</td><td>' + (h.assessment_date || '') + '</td><td>' + (h.height_cm || '-') + '</td><td>' + (h.weight_kg || '-') + '</td><td>' + (h.fatigue_last_month || '-') + '</td><td>' + (h.sleep_quality || '-') + '</td><td>' + (h.weekly_exercise_freq || '-') + '</td><td>' + (h.past_medical_history || '-') + '</td></tr>';
      }).join('');
    });
  }

  function loadAppointmentsPage() {
    fillCustomerSelect('apt-customer');
    fillProjectSelect('apt-project', true);
    fillEquipmentSelect('apt-equipment');
    fillStaffSelect('apt-staff');
    get('/api/appointments').then(function (list) {
      var tbody = document.getElementById('apt-list');
      tbody.innerHTML = (list || []).map(function (a) {
        var cancelBtn = a.status === 'scheduled' ? '<button class="btn btn-small btn-danger" data-cancel="' + a.id + '">取消</button>' : '';
        return '<tr><td>' + (a.customer_name || '') + '</td><td>' + (a.project_name || '-') + '</td><td>' + (a.equipment_name || '-') + '</td><td>' + (a.staff_name || '-') + '</td><td>' + (a.appointment_date || '') + '</td><td>' + (a.start_time || '') + '~' + (a.end_time || '') + '</td><td>' + (a.status || '') + '</td><td>' + cancelBtn + '</td></tr>';
      }).join('');
      tbody.querySelectorAll('[data-cancel]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          post('/api/appointments/' + btn.dataset.cancel + '/cancel').then(function () { loadAppointmentsPage(); });
        });
      });
    });
  }

  function loadCheckinsPage() {
    fillCustomerSelect('checkin-customer');
    var now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.getElementById('checkin-time').value = now.toISOString().slice(0, 16);
    get('/api/visit-checkins').then(function (list) {
      var tbody = document.getElementById('checkin-list');
      tbody.innerHTML = (list || []).map(function (v) {
        return '<tr><td>' + (v.customer_name || '') + '</td><td>' + (v.checkin_time || '') + '</td><td>' + (v.purpose || '-') + '</td><td>' + (v.notes || '-') + '</td></tr>';
      }).join('');
    });
  }


  function checkAppointmentAvailability() {
    var date = document.getElementById('apt-date').value;
    var projectId = document.getElementById('apt-project').value;
    if (!date || !projectId) {
      document.getElementById('apt-availability').textContent = '请先选择日期和项目';
      return;
    }
    get('/api/appointments/free-slots?date=' + encodeURIComponent(date) + '&project_id=' + encodeURIComponent(projectId)).then(function (res) {
      if (res.error) { document.getElementById('apt-availability').textContent = res.error; return; }
      document.getElementById('apt-availability').innerHTML = (res || []).map(function (s) {
        return '<button class="btn btn-small btn-secondary" data-slot="' + s.start_time + ',' + s.end_time + '">' + s.start_time + '-' + s.end_time + ' (设备余量' + s.remaining_equipment + ' 人员' + s.available_staff_count + ')</button>';
      }).join(' ');
      document.querySelectorAll('[data-slot]').forEach(function (b) {
        b.addEventListener('click', function () {
          var t = b.dataset.slot.split(',');
          document.getElementById('apt-start').value = t[0];
          document.getElementById('apt-end').value = t[1];
        });
      });
    });
  }

  function loadAvailableOptions() {
    var date = document.getElementById('apt-date').value;
    var start = document.getElementById('apt-start').value;
    var end = document.getElementById('apt-end').value;
    var projectId = document.getElementById('apt-project').value;
    if (!date || !start || !end || !projectId) { showMsg('apt-msg', '请先选择项目和时段', true); return; }
    get('/api/appointments/available-options?date=' + encodeURIComponent(date) + '&start_time=' + encodeURIComponent(start) + '&end_time=' + encodeURIComponent(end) + '&project_id=' + encodeURIComponent(projectId)).then(function (res) {
      if (res.error) { showMsg('apt-msg', res.error, true); return; }
      var eqSel = document.getElementById('apt-equipment');
      var stSel = document.getElementById('apt-staff');
      eqSel.innerHTML = '<option value="">不指定设备</option>' + (res.available_equipment || []).map(function (e) { return '<option value="' + e.id + '">' + e.name + '</option>'; }).join('');
      stSel.innerHTML = '<option value="">不指定人员</option>' + (res.available_staff || []).map(function (s) { return '<option value="' + s.id + '">' + s.name + '</option>'; }).join('');
    });
  }

  function loadHomeAppointmentsPage() {
    fillCustomerSelect('home-customer');
    fillProjectSelect('home-project', true);
    fillStaffSelect('home-staff');
    get('/api/home-appointments').then(function (list) {
      var tbody = document.getElementById('home-list');
      tbody.innerHTML = (list || []).map(function (a) {
        return '<tr><td>' + (a.customer_name || '') + '</td><td>' + (a.project_name || '-') + '</td><td>' + (a.appointment_date || '') + '</td><td>' + (a.start_time || '') + '~' + (a.end_time || '') + '</td><td>' + (a.location || '-') + '</td><td>' + (a.staff_name || '-') + '</td><td>' + (a.status || '') + '</td></tr>';
      }).join('');
    });
  }

  function loadUsagePage() {
    fillCustomerSelect('usage-customer');
    fillEquipmentSelect('usage-equipment');
    get('/api/equipment-usage').then(function (list) {
      var tbody = document.getElementById('usage-list');
      tbody.innerHTML = (list || []).map(function (u) {
        return '<tr><td>' + (u.customer_name || '') + '</td><td>' + (u.equipment_name || '') + '</td><td>' + (u.usage_date || '') + '</td><td>' + (u.duration_minutes || '-') + '</td><td>' + (u.operator || '-') + '</td></tr>';
      }).join('');
    });
  }

  function loadSurveysPage() {
    fillCustomerSelect('survey-customer');
  }

  document.querySelectorAll('.sidebar a').forEach(function (a) {
    a.addEventListener('click', function (e) { e.preventDefault(); showPage(a.dataset.page); });
  });

  document.getElementById('btn-customer-search').addEventListener('click', loadCustomers);
  document.getElementById('btn-customer-add').addEventListener('click', function () { openCustomerModal(null); });
  document.getElementById('btn-modal-cancel').addEventListener('click', function () { document.getElementById('modal-customer').classList.add('hide'); });
  document.getElementById('btn-modal-save').addEventListener('click', function () {
    var id = document.getElementById('modal-customer-id').value;
    var body = {
      name: document.getElementById('mc-name').value,
      id_card: document.getElementById('mc-id_card').value,
      phone: document.getElementById('mc-phone').value,
      email: document.getElementById('mc-email').value,
      address: document.getElementById('mc-address').value,
      gender: document.getElementById('mc-gender').value,
      birth_date: document.getElementById('mc-birth_date').value || null,
      medical_history: document.getElementById('mc-medical_history').value,
      allergies: document.getElementById('mc-allergies').value,
      diet_habits: document.getElementById('mc-diet_habits').value,
      chronic_diseases: document.getElementById('mc-chronic_diseases').value,
      health_status: document.getElementById('mc-health_status').value,
      therapy_contraindications: document.getElementById('mc-therapy_contraindications').value
    };
    (id ? put('/api/customers/' + id, body) : post('/api/customers', body)).then(function (res) {
      if (res.error) { showMsg('customer-msg', res.error, true); return; }
      document.getElementById('modal-customer').classList.add('hide');
      showMsg('customer-msg', res.message || '保存成功');
      loadCustomers();
    });
  });

  document.getElementById('btn-health-save').addEventListener('click', function () {
    var cid = document.getElementById('health-customer').value;
    if (!cid) { showMsg('health-msg', '请选择客户', true); return; }
    var body = {
      customer_id: parseInt(cid, 10),
      assessment_date: document.getElementById('health-date').value,
      height_cm: document.getElementById('health-height').value || null,
      weight_kg: document.getElementById('health-weight').value || null,
      allergy_history: document.getElementById('health-allergy-history').value || null,
      smoking_status: document.getElementById('health-smoking-status').value || null,
      drinking_status: document.getElementById('health-drinking-status').value || null,
      fatigue_last_month: document.getElementById('health-fatigue-last-month').value || null,
      sleep_quality: document.getElementById('health-sleep-quality').value || null,
      sleep_hours: document.getElementById('health-sleep-hours').value || null,
      blood_pressure_test: document.getElementById('health-blood-pressure-test').value || null,
      blood_lipid_test: document.getElementById('health-blood-lipid-test').value || null,
      chronic_pain: document.getElementById('health-chronic-pain').value || null,
      weekly_exercise_freq: document.getElementById('health-weekly-exercise-freq').value || null,
      past_medical_history: document.getElementById('health-symptoms').value || null,
      family_history: document.getElementById('health-diagnosis').value || null,
      notes: document.getElementById('health-notes').value || null
      assessor: healthValue('ha-assessor'),
      age: healthValue('ha-age'),
      height_cm: healthValue('ha-height-cm', 'health-height'),
      weight_kg: healthValue('ha-weight-kg', 'health-weight'),
      address: healthValue('ha-address'),
      past_medical_history: healthValue('ha-past-medical-history', 'health-symptoms'),
      family_history: healthValue('ha-family-history', 'health-diagnosis'),
      allergy_history: healthValue('ha-allergy-history'),
      allergy_details: healthValue('ha-allergy-details'),
      smoking_status: healthValue('ha-smoking-status'),
      smoking_years: healthValue('ha-smoking-years'),
      cigarettes_per_day: healthValue('ha-cigarettes-per-day'),
      drinking_status: healthValue('ha-drinking-status'),
      drinking_years: healthValue('ha-drinking-years'),
      fatigue_last_month: healthValue('ha-fatigue-last-month'),
      sleep_quality: healthValue('ha-sleep-quality', 'health-bp'),
      sleep_hours: healthValue('ha-sleep-hours'),
      blood_pressure_test: healthValue('ha-blood-pressure-test'),
      blood_lipid_test: healthValue('ha-blood-lipid-test'),
      chronic_pain: healthValue('ha-chronic-pain'),
      pain_details: healthValue('ha-pain-details'),
      exercise_methods: healthValue('ha-exercise-methods'),
      weekly_exercise_freq: healthValue('ha-weekly-exercise-freq'),
      health_needs: healthValue('ha-health-needs'),
      notes: healthValue('ha-notes', 'health-notes')
    };
    post('/api/health-assessments', body).then(function (res) {
      if (res.error) { showMsg('health-msg', res.error, true); return; }
      showMsg('health-msg', res.message);
      loadHealthPage();
    });
  });

  document.getElementById('btn-apt-check').addEventListener('click', checkAppointmentAvailability);
  document.getElementById('btn-apt-options').addEventListener('click', loadAvailableOptions);

  document.getElementById('btn-apt-save').addEventListener('click', function () {
    var body = {
      customer_id: document.getElementById('apt-customer').value,
      project_id: document.getElementById('apt-project').value,
      equipment_id: document.getElementById('apt-equipment').value,
      staff_id: document.getElementById('apt-staff').value,
      appointment_date: document.getElementById('apt-date').value,
      start_time: document.getElementById('apt-start').value,
      end_time: document.getElementById('apt-end').value,
      notes: document.getElementById('apt-notes').value
    };
    if (!body.customer_id || !body.project_id || !body.appointment_date || !body.start_time || !body.end_time) {
      showMsg('apt-msg', '请填写必填项', true);
      return;
    }
    post('/api/appointments', body).then(function (res) {
      if (res.error) { showMsg('apt-msg', res.error, true); return; }
      showMsg('apt-msg', res.message);
      loadAppointmentsPage();
    });
  });

  document.getElementById('btn-checkin-save').addEventListener('click', function () {
    var cid = document.getElementById('checkin-customer').value;
    if (!cid) { showMsg('checkin-msg', '请选择客户', true); return; }
    var t = document.getElementById('checkin-time').value;
    if (!t) {
      var d = new Date();
      t = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0') + ' ' + String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
    }
    var body = {
      customer_id: parseInt(cid, 10),
      checkin_time: t.replace('T', ' ').slice(0, 16),
      purpose: document.getElementById('checkin-purpose').value,
      notes: document.getElementById('checkin-notes').value
    };
    post('/api/visit-checkins', body).then(function (res) {
      if (res.error) { showMsg('checkin-msg', res.error, true); return; }
      showMsg('checkin-msg', res.message);
      loadCheckinsPage();
    });
  });

  document.getElementById('btn-home-save').addEventListener('click', function () {
    var body = {
      customer_id: document.getElementById('home-customer').value,
      project_id: document.getElementById('home-project').value,
      staff_id: document.getElementById('home-staff').value,
      appointment_date: document.getElementById('home-date').value,
      start_time: document.getElementById('home-start').value,
      end_time: document.getElementById('home-end').value,
      location: document.getElementById('home-location').value,
      contact_person: document.getElementById('home-contact-person').value,
      contact_phone: document.getElementById('home-contact-phone').value,
      notes: document.getElementById('home-notes').value
    };
    if (!body.customer_id || !body.project_id || !body.appointment_date || !body.start_time || !body.end_time || !body.location) {
      showMsg('home-msg', '请填写必填项', true); return;
    }
    post('/api/home-appointments', body).then(function (res) {
      if (res.error) { showMsg('home-msg', res.error, true); return; }
      showMsg('home-msg', res.message);
      loadHomeAppointmentsPage();
    });
  });

  document.getElementById('btn-usage-save').addEventListener('click', function () {
    var body = {
      customer_id: document.getElementById('usage-customer').value,
      equipment_id: document.getElementById('usage-equipment').value,
      usage_date: document.getElementById('usage-date').value,
      duration_minutes: document.getElementById('usage-duration').value || null,
      parameters: document.getElementById('usage-params').value,
      operator: document.getElementById('usage-operator').value
    };
    if (!body.customer_id || !body.equipment_id || !body.usage_date) {
      showMsg('usage-msg', '请选择客户、设备和日期', true);
      return;
    }
    post('/api/equipment-usage', body).then(function (res) {
      if (res.error) { showMsg('usage-msg', res.error, true); return; }
      showMsg('usage-msg', res.message);
      loadUsagePage();
    });
  });

  document.getElementById('btn-survey-save').addEventListener('click', function () {
    var cid = document.getElementById('survey-customer').value;
    if (!cid) { showMsg('survey-msg', '请选择客户', true); return; }
    var body = {
      customer_id: parseInt(cid, 10),
      service_rating: document.getElementById('survey-service').value || 5,
      equipment_rating: document.getElementById('survey-equipment').value || 5,
      environment_rating: document.getElementById('survey-env').value || 5,
      staff_rating: document.getElementById('survey-staff').value || 5,
      overall_rating: document.getElementById('survey-overall').value || 5,
      feedback: document.getElementById('survey-feedback').value,
      suggestions: document.getElementById('survey-feedback').value
    };
    post('/api/satisfaction-surveys', body).then(function (res) {
      if (res.error) { showMsg('survey-msg', res.error, true); return; }
      showMsg('survey-msg', res.message);
    });
  });

  document.getElementById('btn-export-customers').addEventListener('click', function () {
    get('/api/export/customers').then(function (data) {
      if (data.download_url) window.location.href = data.download_url;
      showMsg('export-msg', '已触发下载');
    });
  });
  document.getElementById('btn-export-appointments').addEventListener('click', function () {
    get('/api/export/appointments').then(function (data) {
      if (data.download_url) window.location.href = data.download_url;
      showMsg('export-msg', '已触发下载');
    });
  });
  document.getElementById('btn-export-usage').addEventListener('click', function () {
    get('/api/export/equipment-usage').then(function (data) {
      if (data.download_url) window.location.href = data.download_url;
      showMsg('export-msg', '已触发下载');
    });
  });

  document.getElementById('btn-backup-now').addEventListener('click', function () {
    post('/api/system/backup', {}).then(function (res) {
      if (res.error || res.status === 'failed') { showMsg('export-msg', res.message || res.error || '备份失败', true); return; }
      showMsg('export-msg', '备份成功：' + (res.filename || ''));
    });
  });

  document.getElementById('btn-search').addEventListener('click', function () {
    var q = document.getElementById('search-q').value.trim();
    var type = document.getElementById('search-type').value;
    var url = '/api/search?type=' + type + (q ? '&q=' + encodeURIComponent(q) : '');
    get(url).then(function (data) {
      var html = '';
      var labels = { customers: '客户信息', health_records: '健康档案', appointments: '预约记录', visit_checkins: '来访签到', equipment_usage: '仪器使用', surveys: '满意度' };
      var cols = {
        customers: ['name', 'id_card', 'phone', 'address'],
        health_records: ['customer_name', 'record_date', 'height_cm', 'weight_kg', 'blood_pressure', 'symptoms', 'diagnosis'],
        appointments: ['customer_name', 'equipment_name', 'appointment_date', 'start_time', 'end_time', 'status'],
        visit_checkins: ['customer_name', 'checkin_time', 'purpose', 'notes'],
        equipment_usage: ['customer_name', 'equipment_name', 'usage_date', 'duration_minutes', 'operator'],
        surveys: ['customer_name', 'overall_rating', 'feedback', 'survey_date']
      };
      Object.keys(labels).forEach(function (key) {
        var arr = data[key];
        if (!arr || !arr.length) return;
        html += '<div class="result-section"><h3>' + labels[key] + ' (' + arr.length + ')</h3><table><thead><tr>';
        var c = cols[key] || Object.keys(arr[0] || {});
        c.forEach(function (k) { html += '<th>' + k + '</th>'; });
        html += '</tr></thead><tbody>';
        arr.forEach(function (row) {
          html += '<tr>';
          c.forEach(function (k) { html += '<td>' + (row[k] != null ? row[k] : '') + '</td>'; });
          html += '</tr>';
        });
        html += '</tbody></table></div>';
      });
      document.getElementById('search-result').innerHTML = html || '<p style="color:#666">无结果</p>';
    });
  });

  var today = new Date().toISOString().slice(0, 10);
  document.getElementById('health-date').value = today;
  document.getElementById('apt-date').value = today;
  document.getElementById('home-date').value = today;
  document.getElementById('usage-date').value = today;

  showPage('home');
})();
