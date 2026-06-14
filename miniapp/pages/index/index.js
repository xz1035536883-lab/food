const api = require('../../utils/api');
const util = require('../../utils/util');
const app = getApp();

Page({
  data: {
    imagePath: '',
    loading: false,
    isLoggedIn: false,
    summary: {
      total: null,
      target: null,
    },
    remainingCalorie: null,
    intakeScore: '--',
    scoreLabel: '待评估',
    progressWidth: '0%',
    streakDays: 0,
    recentFoodName: '暂无识别',
    recentFoodTime: '今天开始记录',
    coachTitle: '晚餐建议摄入优先低脂、适量蛋白，建议适量增加全谷物',
    coachAuthor: '营养师 Luna',
  },

  onShow() {
    this.setData({ isLoggedIn: app.isLoggedIn() });
    this.loadDashboard();
  },

  resetGuestView(messageState = '登录后查看') {
    this.setData({
      isLoggedIn: false,
      summary: { total: null, target: null },
      remainingCalorie: null,
      intakeScore: '--',
      scoreLabel: messageState,
      progressWidth: '0%',
      streakDays: 0,
      recentFoodName: '授权后查看最近识别',
      recentFoodTime: '点击“我的”先登录',
      coachTitle: '授权后可以同步预算、连续记录和饮食建议。',
      coachAuthor: 'Calm Nutrition Lab',
      loading: false,
    });
  },

  async loadDashboard() {
    const userInfo = app.globalData.userInfo || wx.getStorageSync('userInfo') || {};
    const target = userInfo.daily_calorie_target || 1680;

    if (!app.isLoggedIn()) {
      this.resetGuestView('登录后查看');
      return;
    }

    const today = util.getToday();
    const last7Dates = this.getRecentDates(today, 7);

    try {
      const [summary, recordsRes, recentSummaries] = await Promise.all([
        api.getDailySummary(today),
        api.getRecords(today),
        Promise.all(last7Dates.map((date) => api.getDailySummary(date).catch(() => ({ total: 0 })))),
      ]);

      const total = summary.total || 0;
      const targetValue = summary.target || target;
      const remaining = Math.max(targetValue - total, 0);
      const percent = targetValue > 0 ? Math.min(Math.round((total / targetValue) * 100), 100) : 0;
      const recentRecords = recordsRes.records || [];
      const latestRecord = recentRecords[0];
      const streakDays = this.countStreak(recentSummaries);

      this.setData({
        summary: { total, target: targetValue },
        remainingCalorie: remaining,
        intakeScore: total > 0 ? Math.max(60, 100 - Math.abs(percent - 74)) : '--',
        scoreLabel: total === 0 ? '待开始' : (percent <= 80 ? '良好' : (percent <= 100 ? '接近上限' : '已超预算')),
        progressWidth: `${percent}%`,
        streakDays,
        recentFoodName: latestRecord ? latestRecord.food_name : '今天还没有识别记录',
        recentFoodTime: latestRecord ? `今天 ${util.formatTime(latestRecord.created_at)}` : '先拍摄第一餐',
        coachTitle: total === 0
          ? '三餐均衡，蛋白质摄入充足，继续保持。'
          : (remaining > 0
            ? `今天还可摄入 ${remaining} kcal，建议晚餐继续轻盈一些。`
            : `今天已超出 ${total - targetValue} kcal，下一餐尽量简洁。`),
        coachAuthor: '营养师 Luna',
      });
    } catch (err) {
      if (err.message === '请先登录') {
        this.resetGuestView('登录后查看');
        return;
      }
      this.setData({
        summary: { total: null, target: null },
        remainingCalorie: null,
        intakeScore: '--',
        scoreLabel: '暂不可用',
        progressWidth: '0%',
        streakDays: 0,
        recentFoodName: '暂时无法读取',
        recentFoodTime: '稍后重试',
        coachTitle: '网络恢复后会同步今日预算和最近记录。',
        coachAuthor: 'Calm Nutrition Lab',
      });
    }
  },

  getRecentDates(endDate, days) {
    const result = [];
    const end = new Date(endDate);

    for (let index = days - 1; index >= 0; index -= 1) {
      result.push(util.formatDate(new Date(end.getTime() - index * 86400000)));
    }

    return result;
  },

  countStreak(summaries) {
    let streak = 0;

    for (let index = summaries.length - 1; index >= 0; index -= 1) {
      if ((summaries[index].total || 0) > 0) streak += 1;
      else break;
    }

    return streak;
  },

  takePhoto() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['camera'],
      success: (res) => {
        const tempPath = res.tempFiles[0].tempFilePath;
        this.setData({ imagePath: tempPath });
        this.recognizeFood(tempPath);
      },
      fail: (err) => {
        if (err.errMsg.indexOf('cancel') === -1) {
          wx.showToast({ title: '拍照失败', icon: 'none' });
        }
      },
    });
  },

  chooseImage() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album'],
      success: (res) => {
        const tempPath = res.tempFiles[0].tempFilePath;
        this.setData({ imagePath: tempPath });
        this.recognizeFood(tempPath);
      },
      fail: (err) => {
        if (err.errMsg.indexOf('cancel') === -1) {
          wx.showToast({ title: '选择图片失败', icon: 'none' });
        }
      },
    });
  },

  goToRecordPage() {
    wx.switchTab({ url: '/pages/record/record' });
  },

  resetImage() {
    this.setData({ imagePath: '', loading: false });
  },

  async recognizeFood(filePath) {
    if (!app.isLoggedIn()) {
      wx.showToast({ title: '请先去「我的」授权登录', icon: 'none' });
      return;
    }

    this.setData({ loading: true });

    try {
      const result = await api.recognizeFood(filePath);
      this.setData({ loading: false });

      if (!result.foods || result.foods.length === 0) {
        wx.showModal({
          title: '识别结果',
          content: '未能识别出食物，请尝试拍摄更清晰的照片',
          showCancel: false,
        });
        this.setData({ imagePath: '' });
        return;
      }

      app.globalData.recognitionData = {
        foods: result.foods,
        imagePath: filePath,
      };
      wx.navigateTo({ url: '/pages/result/result' });
    } catch (err) {
      if (err.message === '请先登录') {
        this.resetGuestView('登录后查看');
      } else {
        this.setData({ loading: false });
      }
      wx.showModal({
        title: '识别失败',
        content: err.message || '请检查网络连接后重试',
        showCancel: false,
      });
    }
  },
});
