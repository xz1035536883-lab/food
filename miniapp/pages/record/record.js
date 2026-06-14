const api = require('../../utils/api');
const util = require('../../utils/util');
const app = getApp();

Page({
  data: {
    isLoggedIn: false,
    currentDate: '',
    displayDate: '',
    records: [],
    summary: {
      total: null,
      target: null,
      breakfast: null,
      lunch: null,
      dinner: null,
      snack: null,
    },
    activeFilter: 'all',
    progressPercent: 0,
    progressColor: '#6F9F72',
    trendData: [],
    weightTrendData: [],
    weightSummary: {
      latest_weight: null,
      latest_date: '',
      change_7d: 0,
      records_count: 0,
    },
    mealBreakdown: [],
    dashboardCards: [],
  },

  onShow() {
    const today = util.getToday();
    this.setData({ currentDate: today, isLoggedIn: app.isLoggedIn() });
    this.updateDisplayDate(today);
    this.loadData();
  },

  async loadData() {
    if (!app.isLoggedIn()) {
      this.setData({
        records: [],
        summary: {
          total: null,
          target: null,
          breakfast: null,
          lunch: null,
          dinner: null,
          snack: null,
        },
        progressPercent: 0,
        trendData: [],
        weightTrendData: [],
        weightSummary: {
          latest_weight: null,
          latest_date: '',
          change_7d: 0,
          records_count: 0,
        },
        mealBreakdown: [],
        dashboardCards: [],
      });
      return;
    }
    const { currentDate, activeFilter } = this.data;
    const mealType = activeFilter === 'all' ? null : activeFilter;
    const trendDates = this.getRecentDates(currentDate, 7);

    try {
      util.showLoading('加载中...');

      const [recordsRes, summaryRes, trendRes, weightRes, weightSummary] = await Promise.all([
        api.getRecords(currentDate, mealType),
        api.getDailySummary(currentDate),
        Promise.all(trendDates.map((date) => api.getDailySummary(date).catch(() => ({ total: 0, target: 0 })))),
        api.getWeightRecords(trendDates[0], currentDate),
        api.getWeightSummary(14),
      ]);

      util.hideLoading();

      const records = recordsRes.records || [];
      this.setData({
        records,
        summary: summaryRes,
        weightSummary,
      });

      this.updateProgress();
      this.buildDashboard(records, summaryRes, trendDates, trendRes, weightRes.records || []);
    } catch (err) {
      util.hideLoading();
      if (err.message === '请先登录') {
        this.setData({
          isLoggedIn: false,
          records: [],
          summary: {
            total: null,
            target: null,
            breakfast: null,
            lunch: null,
            dinner: null,
            snack: null,
          },
          progressPercent: 0,
          trendData: [],
          weightTrendData: [],
          weightSummary: {
            latest_weight: null,
            latest_date: '',
            change_7d: 0,
            records_count: 0,
          },
          mealBreakdown: [],
          dashboardCards: [],
        });
      }
      wx.showToast({ title: err.message, icon: 'none' });
    }
  },

  updateProgress() {
    const { summary } = this.data;
    const target = summary.target || 1;
    const percent = Math.min((summary.total / target) * 100, 100);
    const color = util.getCalorieColor(percent);
    this.setData({
      progressPercent: percent,
      progressColor: color,
    });
  },

  buildDashboard(records, summary, trendDates, trendRes, weightRecords) {
    const maxTrend = Math.max(...trendRes.map((item) => item.total || 0), 1);
    const trendData = trendDates.map((date, index) => {
      const total = trendRes[index].total || 0;
      return {
        date,
        label: date.slice(5).replace('-', '/'),
        total,
        height: `${Math.max(20, Math.round((total / maxTrend) * 140))}rpx`,
        active: date === this.data.currentDate,
      };
    });

    const mealList = [
      { key: 'breakfast', label: '早餐', value: summary.breakfast || 0 },
      { key: 'lunch', label: '午餐', value: summary.lunch || 0 },
      { key: 'dinner', label: '晚餐', value: summary.dinner || 0 },
      { key: 'snack', label: '加餐', value: summary.snack || 0 },
    ];
    const total = summary.total || 0;
    const weightMap = {};
    weightRecords.forEach((item) => {
      weightMap[item.record_date] = item.weight;
    });
    const validWeights = weightRecords.map((item) => item.weight);
    const maxWeight = validWeights.length > 0 ? Math.max(...validWeights) : 0;
    const minWeight = validWeights.length > 0 ? Math.min(...validWeights) : 0;
    const weightRange = Math.max(maxWeight - minWeight, 1);
    const weightTrendData = trendDates.map((date) => {
      const value = weightMap[date];
      return {
        label: date.slice(5).replace('-', '/'),
        value,
        height: value ? `${Math.max(24, Math.round(((value - minWeight) / weightRange) * 120) + 24)}rpx` : '18rpx',
        active: date === this.data.currentDate,
      };
    });
    const mealBreakdown = mealList.map((item) => ({
      ...item,
      percent: total > 0 ? Math.round((item.value / total) * 100) : 0,
      width: `${total > 0 ? Math.max(8, Math.round((item.value / total) * 100)) : 8}%`,
    }));
    const remaining = Math.max((summary.target || 0) - total, 0);
    const highestMeal = mealList.reduce((max, item) => (item.value > max.value ? item : max), mealList[0]);
    const avgPerMeal = records.length > 0 ? Math.round(total / records.length) : 0;

    this.setData({
      trendData,
      weightTrendData,
      mealBreakdown,
      dashboardCards: [
        { label: '今日摄入', value: `${total}`, note: 'kcal' },
        { label: '剩余预算', value: `${remaining}`, note: 'kcal' },
        { label: '单餐均值', value: `${avgPerMeal}`, note: 'kcal' },
        { label: '最高餐次', value: highestMeal.value > 0 ? highestMeal.label : '--', note: highestMeal.value > 0 ? `${highestMeal.value} kcal` : '暂无' },
      ],
    });
  },

  getRecentDates(endDate, days) {
    const result = [];
    const end = util.parseDateString(endDate);

    for (let index = days - 1; index >= 0; index -= 1) {
      const date = new Date(end.getTime() - index * 86400000);
      result.push(util.formatDate(date));
    }

    return result;
  },

  updateDisplayDate(date) {
    const today = util.getToday();
    const yesterday = util.formatDate(new Date(Date.now() - 86400000));
    const tomorrow = util.formatDate(new Date(Date.now() + 86400000));

    let display = date;
    if (date === today) display = '今天';
    else if (date === yesterday) display = '昨天';
    else if (date === tomorrow) display = '明天';

    this.setData({ displayDate: display });
  },

  prevDay() {
    const prev = util.addDays(this.data.currentDate, -1);
    this.setData({ currentDate: prev });
    this.updateDisplayDate(prev);
    this.loadData();
  },

  nextDay() {
    const next = util.addDays(this.data.currentDate, 1);
    const today = util.parseDateString(util.getToday()).getTime();
    if (util.parseDateString(next).getTime() > today) return;
    this.setData({ currentDate: next });
    this.updateDisplayDate(next);
    this.loadData();
  },

  onDateChange(e) {
    const date = e.detail.value;
    this.setData({ currentDate: date });
    this.updateDisplayDate(date);
    this.loadData();
  },

  onRecordTap() {},

  filterRecords(e) {
    const filter = e.currentTarget.dataset.filter;
    this.setData({ activeFilter: filter });
    this.loadData();
  },

  async deleteRecord(e) {
    const recordId = e.currentTarget.dataset.id;

    wx.showModal({
      title: '删除确认',
      content: '确定要删除这条记录吗？',
      success: async (res) => {
        if (!res.confirm) return;

        try {
          await api.deleteRecord(recordId);
          wx.showToast({ title: '已删除', icon: 'success' });
          this.loadData();
        } catch (err) {
          wx.showToast({ title: err.message, icon: 'none' });
        }
      },
    });
  },

  goToIndex() {
    wx.switchTab({ url: '/pages/index/index' });
  },

  goToProfile() {
    wx.switchTab({ url: '/pages/profile/profile' });
  },

  formatTime(isoString) {
    return util.formatTime(isoString);
  },

  mealTypeLabel(type) {
    return util.getMealLabel(type);
  },

  mealTypeShort(type) {
    const shorts = { breakfast: '早', lunch: '午', dinner: '晚', snack: '零' };
    return shorts[type] || '食';
  },
});
