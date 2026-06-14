// app.js
App({
  globalData: {
    token: '',
    userInfo: null,
    loginPromise: null,
    apiBase: 'https://your-domain.com',
  },

  onLaunch() {
    // Load cached session
    const token = wx.getStorageSync('token');
    if (token) this.globalData.token = token;
    const userInfo = wx.getStorageSync('userInfo');
    if (userInfo) this.globalData.userInfo = userInfo;
  },

  isLoggedIn() {
    return !!(this.globalData.token && this.globalData.userInfo);
  },

  clearSession() {
    this.globalData.token = '';
    this.globalData.userInfo = null;
    wx.removeStorageSync('token');
    wx.removeStorageSync('userInfo');
    wx.removeStorageSync('weightLossPlan');
  },

  /**
   * Silent auto-login. Returns a Promise that resolves once.
   * Cached promise avoids duplicate concurrent calls.
   */
  login() {
    if (this.globalData.loginPromise) return this.globalData.loginPromise;

    this.globalData.loginPromise = new Promise((resolve) => {
      wx.login({
        success: (res) => {
          if (!res.code) {
            console.error('wx.login returned no code');
            resolve(false);
            return;
          }
          wx.request({
            url: `${this.globalData.apiBase}/api/auth/login`,
            method: 'POST',
            data: { code: res.code },
            success: (resp) => {
              if (resp.data.code === 0) {
                const data = resp.data.data;
                this.globalData.token = data.token;
                this.globalData.userInfo = data.user;
                wx.setStorageSync('token', data.token);
                wx.setStorageSync('userInfo', data.user);
                resolve(true);
              } else {
                this.clearSession();
                console.error('Login failed:', resp.data.message);
                resolve(false);
              }
            },
            fail: (err) => {
              this.clearSession();
              console.error('Login request failed:', err);
              resolve(false);
            },
          });
        },
        fail: (err) => {
          this.clearSession();
          console.error('wx.login error:', err);
          resolve(false);
        },
      });
    });

    // Clean up promise after 10s so retries work
    setTimeout(() => { this.globalData.loginPromise = null; }, 10000);
    return this.globalData.loginPromise;
  },

  getAuthHeader() {
    if (this.globalData.token) {
      return { Authorization: `Bearer ${this.globalData.token}` };
    }
    return {};
  },
});
