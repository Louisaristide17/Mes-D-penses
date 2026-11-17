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
      return const Scaffold(body: Center(child: CircularProgressIndicator(strokeWidth: 2.5)));
    }
    return session.user == null ? const AuthScreen() : const HomeShell();
  }
}
