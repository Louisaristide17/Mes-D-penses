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

  /// Rouvre la session enregistrée. Quoi qu'il arrive, l'écran de chargement se termine :
  /// au pire, l'utilisateur arrive sur l'écran de connexion.
  Future<void> restore() async {
    try {
      await _api.restoreSession();
    } catch (_) {
      // Après une réinstallation, Android peut restaurer des jetons chiffrés avec une clé
      // qui n'existe plus : ils sont illisibles. On les efface et on repart de zéro.
      try {
        await _api.clearSession();
      } catch (_) {}
    }
    if (_api.hasSession) {
      try {
        user = await _api.profile();
      } catch (_) {
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
