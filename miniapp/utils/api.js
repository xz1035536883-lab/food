/**
 * API request wrapper with token management.
 */

const app = getApp();

function handleUnauthorized() {
  // Only clear token, keep cached userInfo
  app.clearToken();
  // Trigger silent re-login to get fresh token
  app.relogin();
}

/**
 * Base request function with auth header and error handling.
 */
function request(url, options = {}) {
  return new Promise((resolve, reject) => {
    const apiBase = app.globalData.apiBase;
    const authHeader = app.getAuthHeader();

    wx.request({
      url: `${apiBase}${url}`,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'content-type': 'application/json',
        ...authHeader,
        ...options.header,
      },
      success(res) {
        if (res.statusCode === 200) {
          if (res.data.code === 0) {
            resolve(res.data.data);
          } else if (res.data.code === 401) {
            handleUnauthorized();
            reject(new Error('请先登录'));
          } else {
            reject(new Error(res.data.message || '请求失败'));
          }
        } else {
          reject(new Error(`服务器错误: ${res.statusCode}`));
        }
      },
      fail(err) {
        reject(new Error(`网络错误: ${err.errMsg}`));
      },
    });
  });
}

/**
 * Upload file with auth header.
 */
function uploadFile(url, filePath, formData = {}) {
  return new Promise((resolve, reject) => {
    const apiBase = app.globalData.apiBase;
    const authHeader = app.getAuthHeader();

    wx.uploadFile({
      url: `${apiBase}${url}`,
      filePath: filePath,
      name: 'image',
      formData: formData,
      header: {
        ...authHeader,
      },
      success(res) {
        try {
          const data = JSON.parse(res.data);
          if (data.code === 0) {
            resolve(data.data);
          } else if (data.code === 401) {
            handleUnauthorized();
            reject(new Error('请先登录'));
          } else {
            reject(new Error(data.message || '上传失败'));
          }
        } catch (e) {
          reject(new Error('解析响应失败'));
        }
      },
      fail(err) {
        reject(new Error(`上传失败: ${err.errMsg}`));
      },
    });
  });
}

// ==================== Auth API ====================

function getProfile() {
  return request('/api/auth/profile');
}

function updateProfile(data) {
  return request('/api/auth/profile', {
    method: 'POST',
    data,
  });
}

// ==================== Food API ====================

function recognizeFood(filePath) {
  return uploadFile('/api/food/recognize', filePath);
}

function searchFoods(keyword) {
  return request('/api/food/search', {
    data: { keyword },
  });
}

// ==================== Diet Record API ====================

function addRecord(data) {
  return request('/api/record', {
    method: 'POST',
    data,
  });
}

function getRecords(date, mealType) {
  let url = `/api/record?record_date=${date}`;
  if (mealType) {
    url += `&meal_type=${mealType}`;
  }
  return request(url);
}

function getDailySummary(date) {
  return request(`/api/record/summary?record_date=${date}`);
}

function deleteRecord(recordId) {
  return request(`/api/record/${recordId}`, {
    method: 'DELETE',
  });
}

function getPlan() {
  return request('/api/auth/plan');
}

function saveWeightRecord(data) {
  return request('/api/weight', {
    method: 'POST',
    data,
  });
}

function getWeightRecords(dateFrom, dateTo, limit) {
  const params = [];
  if (dateFrom) params.push(`date_from=${dateFrom}`);
  if (dateTo) params.push(`date_to=${dateTo}`);
  if (limit) params.push(`limit=${limit}`);
  const query = params.length > 0 ? `?${params.join('&')}` : '';
  return request(`/api/weight${query}`);
}

function getWeightSummary(days) {
  const query = days ? `?days=${days}` : '';
  return request(`/api/weight/summary${query}`);
}

module.exports = {
  request,
  uploadFile,
  getProfile,
  updateProfile,
  recognizeFood,
  searchFoods,
  addRecord,
  getRecords,
  getDailySummary,
  deleteRecord,
  getPlan,
  saveWeightRecord,
  getWeightRecords,
  getWeightSummary,
};
