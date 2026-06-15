// app.js
App({
  globalData: {
    token: '',
    userInfo: null,
    loginPromise: null,
    apiBase: 'https://silentzz.online',
  },

  onLaunch() {
    // Load cached session
    const token = wx.getStorageSync('token');
    if (token) this.globalData.token = token;
    const userInfo = wx.getStorageSync('userInfo');
    if (userInfo) this.globalData.userInfo = userInfo;

    // Auto-login silently if we have a cached token
    if (token) {
      this.relogin();
    }
  },

  isLoggedIn() {
    return !!(this.globalData.token && this.globalData.userInfo);
  },

  /**
   * Clear ONLY the auth token, keep userInfo.
   * Used when token expires (401) — we keep cached data and re-login.
   */
  clearToken() {
    this.globalData.token = '';
    wx.removeStorageSync('token');
  },

  /**
   * Full logout — clear all cached data.
   */
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
                this.clearToken();
                console.error('Login failed:', resp.data.message);
                resolve(false);
              }
            },
            fail: (err) => {
              this.clearToken();
              console.error('Login request failed:', err);
              resolve(false);
            },
          });
        },
        fail: (err) => {
          this.clearToken();
          console.error('wx.login error:', err);
          resolve(false);
        },
      });
    });

    // Clean up promise after 10s so retries work
    setTimeout(() => { this.globalData.loginPromise = null; }, 10000);
    return this.globalData.loginPromise;
  },

  /**
   * Silent re-login: get fresh token, merge backend data with local cache.
   * Does NOT clear userInfo — keeps local edits safe.
   */
  relogin() {
    if (this.globalData.loginPromise) return this.globalData.loginPromise;

    this.globalData.loginPromise = new Promise((resolve) => {
      wx.login({
        success: (res) => {
          if (!res.code) {
            this.clearToken();
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
                // Merge: backend data is authoritative for profile fields
                this.globalData.userInfo = { ...this.globalData.userInfo, ...data.user };
                wx.setStorageSync('token', data.token);
                wx.setStorageSync('userInfo', this.globalData.userInfo);
                resolve(true);
              } else {
                this.clearToken();
                resolve(false);
              }
            },
            fail: () => {
              // Network error — keep existing token (might work again)
              resolve(false);
            },
          });
        },
        fail: () => {
          resolve(false);
        },
      });
    });

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
