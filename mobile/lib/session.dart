import 'package:flutter/foundation.dart';

import 'api.dart';
import 'models.dart';

/// État de connexion, partagé par toute l'application.
class Session extends ChangeNotifier {
  Session(this._api) {
    _api.onSessionExpired = _expire;
  }

  final ApiClient _api;

  User? user;
  bool loading = true;

  Future<void> restore() async {
    await _api.restoreSession();
    if (_api.hasSession) {
      try {
        user = await _api.profile();
      } on ApiException {
        user = null;
      }
    }
    loading = false;
    notifyListeners();
  }

  Future<void> login(String email, String password) async {
    user = await _api.login(email, password);
    notifyListeners();
  }

  Future<void> register(String name, String email, String password) async {
    user = await _api.register(name, email, password);
    notifyListeners();
  }

  void setUser(User updated) {
    user = updated;
    notifyListeners();
  }

  Future<void> logout() async {
    await _api.clearSession();
    _expire();
  }

  void _expire() {
    user = null;
    notifyListeners();
  }
}
