// pages/result/result.js
const api = require('../../utils/api');
const util = require('../../utils/util');
const app = getApp();

Page({
  data: {
    imagePath: '',
    foods: [],
    mealTypes: [
      { value: 'breakfast', label: '早餐' },
      { value: 'lunch', label: '午餐' },
      { value: 'dinner', label: '晚餐' },
      { value: 'snack', label: '零食' },
    ],
  },

  onLoad() {
    // Read data from globalData (passed by index page)
    const data = app.globalData.recognitionData;
    if (data) {
      const foods = (data.foods || []).map((item, index) => ({
        ...item,
        confidencePct: Math.round((item.confidence || 0) * 100),
        mealIndex: 0,
        saved: false,
      }));
      this.setData({ foods, imagePath: data.imagePath || '' });
      // Clean up after reading
      app.globalData.recognitionData = null;
    }
  },

  onWeightChange(e) {
    const index = e.currentTarget.dataset.index;
    const value = parseInt(e.detail.value) || 0;
    const foods = this.data.foods;
    foods[index].weight = value;
    // Recalculate calories: per-100g * weight(g) / 100
    const per100g = foods[index].nutrition.calories;
    foods[index].calories = Math.round(per100g * value) / 100;
    this.setData({ foods });
  },

  onMealChange(e) {
    const index = e.currentTarget.dataset.index;
    const mealIndex = parseInt(e.detail.value);
    const foods = this.data.foods;
    foods[index].mealIndex = mealIndex;
    this.setData({ foods });
  },

  async saveRecord(e) {
    const index = e.currentTarget.dataset.index;
    const food = this.data.foods[index];
    const mealType = this.data.mealTypes[food.mealIndex].value;

    try {
      wx.showLoading({ title: '保存中...' });

      await api.addRecord({
        food_id: 0,
        food_name: food.name,
        image_url: '', // Temp path not meaningful for storage
        weight: food.weight,
        calories: food.calories,
        meal_type: mealType,
        record_date: util.getToday(),
      });

      wx.hideLoading();
      wx.showToast({ title: '保存成功', icon: 'success' });

      const foods = this.data.foods;
      foods[index].saved = true;
      this.setData({ foods });
    } catch (err) {
      wx.hideLoading();
      wx.showToast({ title: err.message || '保存失败', icon: 'none' });
    }
  },

  viewRecords() {
    wx.switchTab({ url: '/pages/record/record' });
  },

  goBack() {
    wx.navigateBack();
  },
});
