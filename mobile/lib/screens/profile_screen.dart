import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api.dart';
import '../session.dart';
import '../theme.dart';
import '../widgets.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 24, 16, 32),
      children: [
        const ScreenHeader(title: 'Profil', subtitle: 'Votre compte et vos réglages.'),
        const SizedBox(height: 16),
        const _IdentityCard(),
        const SizedBox(height: 16),
        const _PasswordCard(),
        const SizedBox(height: 24),
        OutlinedButton.icon(
          style: secondaryButtonStyle(),
          onPressed: () => context.read<Session>().logout(),
          icon: const Icon(Icons.logout, size: 18),
          label: const Text('Se déconnecter'),
        ),
      ],
    );
  }
}

class _IdentityCard extends StatefulWidget {
  const _IdentityCard();

  @override
  State<_IdentityCard> createState() => _IdentityCardState();
}

class _IdentityCardState extends State<_IdentityCard> {
  late final TextEditingController _name;
  late final TextEditingController _email;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    final user = context.read<Session>().user!;
    _name = TextEditingController(text: user.name);
    _email = TextEditingController(text: user.email);
  }

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final name = _name.text.trim();
    final email = _email.text.trim();
    if (name.length < 2 || !email.contains('@')) {
      setState(() => _error = 'Indiquez un nom et une adresse e-mail valides.');
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    final api = context.read<ApiClient>();
    final session = context.read<Session>();
    try {
      session.setUser(await api.updateProfile(name, email));
      if (mounted) showMessage(context, 'Profil mis à jour.');
    } on ApiException catch (failure) {
      if (mounted) setState(() => _error = failure.message);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('Informations personnelles', style: AppText.section),
          const SizedBox(height: 16),
          if (_error != null) ...[Notice(text: _error!), const SizedBox(height: 16)],
          TextField(
            controller: _name,
            textCapitalization: TextCapitalization.words,
            decoration: fieldDecoration('Nom complet'),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            autocorrect: false,
            decoration: fieldDecoration('Adresse e-mail'),
          ),
          const SizedBox(height: 16),
          FilledButton(
            style: primaryButtonStyle(),
            onPressed: _saving ? null : _save,
            child: const Text('Enregistrer'),
          ),
        ],
      ),
    );
  }
}

class _PasswordCard extends StatefulWidget {
  const _PasswordCard();

  @override
  State<_PasswordCard> createState() => _PasswordCardState();
}

class _PasswordCardState extends State<_PasswordCard> {
  final _current = TextEditingController();
  final _next = TextEditingController();
  bool _saving = false;
  String? _error;

  @override
  void dispose() {
    _current.dispose();
    _next.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (_current.text.isEmpty || _next.text.length < 8) {
      setState(() => _error = 'Le nouveau mot de passe doit contenir au moins 8 caractères.');
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    final api = context.read<ApiClient>();
    try {
      await api.changePassword(_current.text, _next.text);
      _current.clear();
      _next.clear();
      if (mounted) showMessage(context, 'Mot de passe modifié.');
    } on ApiException catch (failure) {
      if (mounted) setState(() => _error = failure.message);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('Mot de passe', style: AppText.section),
          const SizedBox(height: 16),
          if (_error != null) ...[Notice(text: _error!), const SizedBox(height: 16)],
          TextField(
            controller: _current,
            obscureText: true,
            decoration: fieldDecoration('Mot de passe actuel'),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _next,
            obscureText: true,
            decoration: fieldDecoration('Nouveau mot de passe', helper: '8 caractères au minimum.'),
          ),
          const SizedBox(height: 16),
          FilledButton(
            style: primaryButtonStyle(),
            onPressed: _saving ? null : _save,
            child: const Text('Modifier le mot de passe'),
          ),
        ],
      ),
    );
  }
}
