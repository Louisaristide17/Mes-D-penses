import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

import 'models.dart';

class ApiException implements Exception {
  const ApiException(this.message, this.status);

  final String message;
  final int status;

  @override
  String toString() => message;
}

/// Conservation des jetons entre deux lancements de l'application.
abstract class TokenStore {
  Future<Map<String, String>?> read();
  Future<void> write(String access, String refresh);
  Future<void> clear();
}

/// Stockage chiffré par le système (Keystore sur Android).
class SecureTokenStore implements TokenStore {
  static const _storage = FlutterSecureStorage();
  static const _accessKey = 'access_token';
  static const _refreshKey = 'refresh_token';

  @override
  Future<Map<String, String>?> read() async {
    final access = await _storage.read(key: _accessKey);
    final refresh = await _storage.read(key: _refreshKey);
    if (access == null || refresh == null) return null;
    return {'access': access, 'refresh': refresh};
  }

  @override
  Future<void> write(String access, String refresh) async {
    await _storage.write(key: _accessKey, value: access);
    await _storage.write(key: _refreshKey, value: refresh);
  }

  @override
  Future<void> clear() async {
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
  }
}

class ApiClient {
  ApiClient({http.Client? client, TokenStore? store})
      : _client = client ?? http.Client(),
        _store = store ?? SecureTokenStore();

  /// 10.0.2.2 désigne la machine hôte depuis l'émulateur Android.
  /// Sur un téléphone réel : flutter run --dart-define=API_URL=http://<adresse>:8000
  static const baseUrl = String.fromEnvironment('API_URL', defaultValue: 'http://10.0.2.2:8000');

  final http.Client _client;
  final TokenStore _store;

  String? _access;
  String? _refresh;
  Future<bool>? _refreshing;

  /// Appelé quand la session ne peut plus être renouvelée.
  void Function()? onSessionExpired;

  bool get hasSession => _access != null;

  Future<void> restoreSession() async {
    final tokens = await _store.read();
    _access = tokens?['access'];
    _refresh = tokens?['refresh'];
  }

  Future<void> _saveSession(Json tokens) async {
    _access = tokens['access_token'] as String;
    _refresh = tokens['refresh_token'] as String;
    await _store.write(_access!, _refresh!);
  }

  Future<void> clearSession() async {
    _access = null;
    _refresh = null;
    await _store.clear();
  }

  Future<http.Response> _send(String method, String path, {Map<String, String>? query, Object? body}) async {
    // L'assistant enchaîne plusieurs appels au modèle de langage : sa réponse peut prendre plus longtemps.
    final timeout = Duration(seconds: path.startsWith('/assistant/') ? 90 : 75;
    final base = Uri.parse('$baseUrl/api/v1$path');
    final uri = (query == null || query.isEmpty) ? base : base.replace(queryParameters: query);
    final request = http.Request(method, uri);
    if (_access != null) request.headers['Authorization'] = 'Bearer $_access';
    if (body != null) {
      request.headers['Content-Type'] = 'application/json';
      request.body = jsonEncode(body);
    }
    try {
      final streamed = await _client.send(request).timeout(timeout);
      return await http.Response.fromStream(streamed);
    } catch (_) {
      throw const ApiException('Connexion au serveur impossible. Vérifiez votre connexion internet.', 0);
    }
  }

  // Plusieurs requêtes peuvent expirer en même temps : un seul renouvellement est lancé.
  Future<bool> _refreshSession() {
    return _refreshing ??= _doRefresh().whenComplete(() => _refreshing = null);
  }

  Future<bool> _doRefresh() async {
    final refresh = _refresh;
    if (refresh == null) return false;
    try {
      final response = await _client
          .post(
            Uri.parse('$baseUrl/api/v1/auth/refresh'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'refresh_token': refresh}),
          )
          .timeout(const Duration(seconds: 20));
      if (response.statusCode != 200) return false;
      await _saveSession(_decode(response) as Json);
      return true;
    } catch (_) {
      return false;
    }
  }

  dynamic _decode(http.Response response) {
    if (response.bodyBytes.isEmpty) return null;
    return jsonDecode(utf8.decode(response.bodyBytes));
  }

  ApiException _toError(http.Response response) {
    var message = 'Une erreur est survenue. Réessayez dans un instant.';
    if (response.statusCode == 422) {
      message = 'Certaines informations sont invalides. Vérifiez le formulaire.';
    } else {
      try {
        final data = _decode(response);
        if (data is Map && data['detail'] is String) message = data['detail'] as String;
      } catch (_) {
        // Réponse sans corps JSON : on garde le message générique.
      }
    }
    return ApiException(message, response.statusCode);
  }

  Future<dynamic> _request(String method, String path, {Map<String, String>? query, Object? body}) async {
    var response = await _send(method, path, query: query, body: body);
    final isAuthRoute = path.startsWith('/auth/');
    if (response.statusCode == 401 && _access != null && !isAuthRoute) {
      final renewed = await _refreshSession();
      if (!renewed) {
        await clearSession();
        onSessionExpired?.call();
        throw const ApiException('Votre session a expiré. Veuillez vous reconnecter.', 401);
      }
      response = await _send(method, path, query: query, body: body);
    }
    if (response.statusCode < 200 || response.statusCode >= 300) throw _toError(response);
    return _decode(response);
  }

  // Comptes

  Future<User> login(String email, String password) async {
    final data = await _request('POST', '/auth/login', body: {'email': email, 'password': password}) as Json;
    await _saveSession(data);
    return User.fromJson(data['user'] as Json);
  }

  Future<User> register(String name, String email, String password) async {
    final data = await _request(
      'POST',
      '/auth/register',
      body: {'name': name, 'email': email, 'password': password},
    ) as Json;
    await _saveSession(data);
    return User.fromJson(data['user'] as Json);
  }

  Future<User> profile() async => User.fromJson(await _request('GET', '/users/me') as Json);

  Future<User> updateProfile(String name, String email) async {
    return User.fromJson(await _request('PATCH', '/users/me', body: {'name': name, 'email': email}) as Json);
  }

  Future<void> changePassword(String current, String next) async {
    await _request('POST', '/users/me/password', body: {'current_password': current, 'new_password': next});
  }

  // Catégories et dépenses

  Future<List<ExpenseCategory>> categories() async {
    final data = await _request('GET', '/categories') as List<dynamic>;
    return data.map((item) => ExpenseCategory.fromJson(item as Json)).toList();
  }

  Future<ExpensePage> expenses({required String dateFrom, required String dateTo, String search = ''}) async {
    final query = {'date_from': dateFrom, 'date_to': dateTo, 'limit': '200'};
    if (search.isNotEmpty) query['q'] = search;
    return ExpensePage.fromJson(await _request('GET', '/expenses', query: query) as Json);
  }

  Future<void> createExpense({required int amount, required String date, required String note, int? categoryId}) async {
    final body = <String, dynamic>{'amount': amount, 'date': date, 'note': note};
    if (categoryId != null) body['category_id'] = categoryId;
    await _request('POST', '/expenses', body: body);
  }

  Future<void> updateExpense(
    int id, {
    required int amount,
    required String date,
    required String note,
    required int categoryId,
  }) async {
    await _request(
      'PATCH',
      '/expenses/$id',
      body: {'amount': amount, 'date': date, 'note': note, 'category_id': categoryId},
    );
  }

  Future<void> deleteExpense(int id) async {
    await _request('DELETE', '/expenses/$id');
  }

  Future<Suggestion> suggestCategory(String note) async {
    return Suggestion.fromJson(await _request('POST', '/expenses/suggest-category', body: {'note': note}) as Json);
  }

  // Budgets et tableau de bord

  Future<List<BudgetStatus>> budgetStatuses(String month) async {
    final data = await _request('GET', '/budgets/status', query: {'month': month}) as List<dynamic>;
    return data.map((item) => BudgetStatus.fromJson(item as Json)).toList();
  }

  Future<void> setBudget({required int categoryId, required String month, required int ceiling}) async {
    await _request('PUT', '/budgets', body: {'category_id': categoryId, 'month': month, 'ceiling': ceiling});
  }

  Future<void> deleteBudget(int id) async {
    await _request('DELETE', '/budgets/$id');
  }

  Future<DashboardSummary> dashboard(String month) async {
    return DashboardSummary.fromJson(await _request('GET', '/dashboard/summary', query: {'month': month}) as Json);
  }

  // Assistant

  Future<AssistantAnswer> askAssistant(String message, int? conversationId) async {
    final body = <String, dynamic>{'message': message};
    if (conversationId != null) body['conversation_id'] = conversationId;
    return AssistantAnswer.fromJson(await _request('POST', '/assistant/messages', body: body) as Json);
  }
}
