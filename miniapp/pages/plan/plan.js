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
      if (cachedPlan) this.setData({ planData: this.normalizePlanData(cachedPlan) });
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

  normalizePlanData(planData) {
    if (!planData) return null;
    const mealBudget = planData.meal_budget || {
      breakfast: planData.breakfast_cal || 0,
      lunch: planData.lunch_cal || 0,
      dinner: planData.dinner_cal || 0,
      snack: planData.snack_cal || 0,
    };
    return {
      ...planData,
      meal_budget: mealBudget,
      protocol: planData.protocol || {
        daily_deficit: planData.daily_deficit || 0,
        weekly_weight_change: planData.daily_deficit ? Number(((planData.daily_deficit * 7) / 7700).toFixed(2)) : 0,
        weigh_in_frequency: '每周 1 次',
        review_cycle: '每 7 天复盘一次记录与体重趋势',
        warning: '避免极低热量、补偿性暴食和连续高强度空腹有氧',
      },
      milestones: planData.milestones || [],
      advice: planData.advice || {
        diet: [],
        exercise: [],
        lifestyle: [],
      },
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

  async generatePlan() {
    if (!app.isLoggedIn()) return;
    const u = this.data.userInfo;
    if (!u.gender || !u.age || !u.height || !u.weight) {
      wx.showToast({ title: '请先完善身体数据', icon: 'none' });
      return;
    }
    if (!u.target_weight) {
      wx.showToast({ title: '请设置目标体重', icon: 'none' });
      return;
    }
    try {
      wx.showLoading({ title: '生成计划...' });
      await api.updateProfile({
        gender: u.gender,
        age: u.age,
        height: u.height,
        weight: u.weight,
        target_weight: u.target_weight,
      });
      const savedUserInfo = {
        ...this.data.userInfo,
        gender: u.gender,
        age: u.age,
        height: u.height,
        weight: u.weight,
        target_weight: u.target_weight,
      };
      app.globalData.userInfo = { ...app.globalData.userInfo, ...savedUserInfo };
      wx.setStorageSync('userInfo', savedUserInfo);
      const result = await api.getPlan();
      wx.hideLoading();
      if (result && result.plan) {
        const profileSummary = this.normalizeProfileSummary(result.profile_summary || this.getProfileSummary(savedUserInfo));
        const normalizedPlanData = this.normalizePlanData(result.plan);
        const nextUserInfo = {
          ...savedUserInfo,
          profile_summary: {
            completion: profileSummary.completion,
            missing_fields: profileSummary.missingFields,
          },
          daily_calorie_target: normalizedPlanData.daily_calorie_target || savedUserInfo.daily_calorie_target,
        };
        this.setData({
          planData: normalizedPlanData,
          userInfo: nextUserInfo,
          profileCompletion: profileSummary.completion,
          missingFields: profileSummary.missingFields,
          missingFieldsText: profileSummary.missingFields.join(' / '),
        });
        app.globalData.userInfo = { ...app.globalData.userInfo, ...nextUserInfo };
        wx.setStorageSync('userInfo', nextUserInfo);
        wx.setStorageSync('weightLossPlan', normalizedPlanData);
        wx.showToast({ title: '计划已生成', icon: 'success' });
      }
    } catch (err) {
      wx.hideLoading();
      if (err.message === '请先登录') {
        this.resetLoggedOutState();
      }
      wx.showToast({ title: err.message || '生成失败', icon: 'none' });
    }
  },

  onTargetChange(e) {
    if (!app.isLoggedIn()) return;
    const dailyCalorieTarget = e.detail.value;
    this.setData({ 'userInfo.daily_calorie_target': dailyCalorieTarget });
    api.updateProfile({ daily_calorie_target: dailyCalorieTarget })
      .then((data) => {
        const userInfo = { ...this.data.userInfo, ...data };
        const profileSummary = this.normalizeProfileSummary(data.profile_summary || this.getProfileSummary(userInfo));
        this.setData({
          userInfo,
          profileCompletion: profileSummary.completion,
          missingFields: profileSummary.missingFields,
          missingFieldsText: profileSummary.missingFields.join(' / '),
        });
        app.globalData.userInfo = { ...app.globalData.userInfo, ...userInfo };
        wx.setStorageSync('userInfo', userInfo);
      })
      .catch((err) => {
        if (err.message === '请先登录') {
          this.resetLoggedOutState();
        }
      });
  },
});
