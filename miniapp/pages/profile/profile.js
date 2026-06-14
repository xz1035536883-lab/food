const api = require('../../utils/api');
const app = getApp();

Page({
  data: {
    isLoggedIn: false,
    userInfo: {
      id: null, nickname: '', avatar_url: '',
      daily_calorie_target: 2000,
      gender: '', age: null, height: null,
      weight: null, target_weight: null,
    },
    planData: null,
    profileCompletion: 0,
    missingFields: [],
    missingFieldsText: '',
    todayWeight: '',
    weightSummary: {
      latest_weight: null,
      latest_date: '',
      change_7d: 0,
      records_count: 0,
    },
  },

  onShow() {
    this.syncUserInfo();
  },

  resetLoggedOutState() {
    this.setData({
      isLoggedIn: false,
      planData: null,
      profileCompletion: 0,
      missingFields: [],
      missingFieldsText: '',
      todayWeight: '',
      weightSummary: {
        latest_weight: null,
        latest_date: '',
        change_7d: 0,
        records_count: 0,
      },
      userInfo: {
        id: null, nickname: '', avatar_url: '',
        daily_calorie_target: 2000,
        gender: '', age: null, height: null,
        weight: null, target_weight: null,
      },
    });
  },

  async handleLogin() {
    wx.showLoading({ title: '登录中...' });
    const success = await app.login();
    wx.hideLoading();
    if (success) {
      this.syncUserInfo();
      wx.showToast({ title: '登录成功', icon: 'success' });
    } else {
      wx.showToast({ title: '登录失败，请重试', icon: 'none' });
    }
  },

  syncUserInfo() {
    const isLoggedIn = app.isLoggedIn();

    let userInfo = app.globalData.userInfo || wx.getStorageSync('userInfo') || {};
    const defaults = {
      id: null, nickname: '', avatar_url: '',
      daily_calorie_target: 2000,
      gender: '', age: null, height: null,
      weight: null, target_weight: null,
    };
    userInfo = { ...defaults, ...userInfo };
    const profileSummary = this.normalizeProfileSummary(userInfo.profile_summary || this.getProfileSummary(userInfo));
    this.setData({
      isLoggedIn,
      userInfo,
      profileCompletion: profileSummary.completion,
      missingFields: profileSummary.missingFields,
      missingFieldsText: profileSummary.missingFields.join(' / '),
    });

    if (isLoggedIn) {
      const cachedPlan = wx.getStorageSync('weightLossPlan');
      if (cachedPlan) this.setData({ planData: cachedPlan });
      this.loadWeightModule();
    }
  },

  async loadWeightModule() {
    try {
      const summary = await api.getWeightSummary(14);
      this.setData({
        weightSummary: summary,
        todayWeight: summary.latest_date === this.getToday() && summary.latest_weight ? String(summary.latest_weight) : '',
      });
    } catch (err) {
      if (err.message === '请先登录') {
        this.resetLoggedOutState();
      }
    }
  },

  getProfileSummary(userInfo) {
    const fields = [
      { key: 'gender', label: '性别' },
      { key: 'age', label: '年龄' },
      { key: 'height', label: '身高' },
      { key: 'weight', label: '当前体重' },
      { key: 'target_weight', label: '目标体重' },
    ];
    const filledCount = fields.filter(({ key }) => !!userInfo[key]).length;
    return {
      completion: Math.round((filledCount / fields.length) * 100),
      missingFields: fields.filter(({ key }) => !userInfo[key]).map(({ label }) => label),
    };
  },

  normalizeProfileSummary(summary) {
    const missingFields = summary.missingFields || summary.missing_fields || [];
    return {
      completion: summary.completion || 0,
      missingFields,
    };
  },

  onGenderChange(e) {
    this.setData({ 'userInfo.gender': e.currentTarget.dataset.gender });
  },

  onFieldInput(e) {
    const field = e.currentTarget.dataset.field;
    const raw = e.detail.value;
    const parsed = raw === '' ? null : (field === 'age' ? parseInt(raw, 10) : parseFloat(raw));
    this.setData({ [`userInfo.${field}`]: parsed });
  },

  onTodayWeightInput(e) {
    this.setData({ todayWeight: e.detail.value });
  },

  getToday() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  },

  async saveTodayWeight() {
    const raw = this.data.todayWeight;
    const weight = raw === '' ? 0 : parseFloat(raw);
    if (!weight || weight < 20 || weight > 500) {
      wx.showToast({ title: '请输入有效体重', icon: 'none' });
      return;
    }
    try {
      wx.showLoading({ title: '记录中...' });
      await api.saveWeightRecord({
        weight,
        record_date: this.getToday(),
        note: '',
      });
      wx.hideLoading();
      wx.showToast({ title: '已记录', icon: 'success' });
      const userInfo = { ...this.data.userInfo, weight };
      this.setData({ userInfo });
      app.globalData.userInfo = { ...app.globalData.userInfo, ...userInfo };
      wx.setStorageSync('userInfo', userInfo);
      this.loadWeightModule();
    } catch (err) {
      wx.hideLoading();
      if (err.message === '请先登录') {
        this.resetLoggedOutState();
      }
      wx.showToast({ title: err.message || '记录失败', icon: 'none' });
    }
  },

  async saveBodyInfo() {
    const u = this.data.userInfo;
    if (!u.gender) {
      wx.showToast({ title: '请选择性别', icon: 'none' });
      return;
    }
    try {
      wx.showLoading({ title: '保存中...' });
      const data = await api.updateProfile({
        gender: u.gender,
        age: u.age,
        height: u.height,
        weight: u.weight,
        target_weight: u.target_weight,
      });
      wx.hideLoading();
      wx.showToast({ title: '保存成功', icon: 'success' });
      app.globalData.userInfo = { ...app.globalData.userInfo, ...data };
      wx.setStorageSync('userInfo', data);
      const userInfo = { ...this.data.userInfo, ...data };
      const profileSummary = this.normalizeProfileSummary(data.profile_summary || this.getProfileSummary(userInfo));
      this.setData({
        userInfo,
        profileCompletion: profileSummary.completion,
        missingFields: profileSummary.missingFields,
        missingFieldsText: profileSummary.missingFields.join(' / '),
      });
    } catch (err) {
      wx.hideLoading();
      if (err.message === '请先登录') {
        this.resetLoggedOutState();
      }
      wx.showToast({ title: err.message || '保存失败', icon: 'none' });
    }
  },

  goToPlan() {
    wx.switchTab({ url: '/pages/plan/plan' });
  },

  goToRecord() {
    wx.switchTab({ url: '/pages/record/record' });
  },

  showAbout() {
    wx.showModal({
      title: '关于我们',
      content: '食物热量识别助手 — 拍照识别食物营养，智能生成减肥计划。',
      showCancel: false,
    });
  },

  showHelp() {
    wx.showModal({
      title: '使用帮助',
      content: '1. 完善身体数据\n2. 生成专属减肥计划\n3. 拍照识别食物热量\n4. 记录每日饮食',
      showCancel: false,
    });
  },

  clearCache() {
    wx.showModal({
      title: '清除缓存',
      content: '将清除本地登录信息和缓存数据',
      success: (res) => {
        if (res.confirm) {
          wx.clearStorage();
          app.clearSession();
          this.resetLoggedOutState();
          wx.showToast({ title: '已清除', icon: 'success' });
        }
      },
    });
  },
});
