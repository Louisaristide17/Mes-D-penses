import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';

import 'api.dart';
import 'screens/auth_screen.dart';
import 'screens/home_shell.dart';
import 'session.dart';
import 'theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  final api = ApiClient();
  final session = Session(api)..restore();
  runApp(
    MultiProvider(
      providers: [
        Provider<ApiClient>.value(value: api),
        ChangeNotifierProvider<Session>.value(value: session),
      ],
      child: const MesDepensesApp(),
    ),
  );
}

class MesDepensesApp extends StatelessWidget {
  const MesDepensesApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Mes Dépenses',
      debugShowCheckedModeBanner: false,
      theme: buildTheme(),
      locale: const Locale('fr'),
      supportedLocales: const [Locale('fr')],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      home: const _Root(),
    );
  }
}

class _Root extends StatelessWidget {
  const _Root();

  @override
  Widget build(BuildContext context) {
    final session = context.watch<Session>();
    if (session.loading) {
      return const _Splash();
    }
    return session.user == null ? const AuthScreen() : const HomeShell();
  }
}

/// Écran affiché pendant l'ouverture de la session. Le serveur peut mettre jusqu'à une minute à se
/// réveiller : on le dit, pour que l'utilisateur ne croie pas l'application bloquée.
class _Splash extends StatelessWidget {
  const _Splash();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 56,
                  height: 56,
                  decoration: BoxDecoration(color: AppColors.primary, borderRadius: BorderRadius.circular(12)),
                  child: const Icon(Icons.account_balance_wallet_outlined, color: Colors.white, size: 28),
                ),
                const SizedBox(height: 24),
                const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2.5)),
                const SizedBox(height: 16),
                const Text('Connexion au serveur', style: AppText.section),
                const SizedBox(height: 8),
                Text(
                  "Après une période d'inactivité, cela peut prendre jusqu'à une minute.",
                  style: AppText.body.copyWith(color: AppColors.muted),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
