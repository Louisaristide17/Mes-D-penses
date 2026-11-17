import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api.dart';
import '../session.dart';
import '../theme.dart';
import '../widgets.dart';

const _minPassword = 8;

/// Connexion et création de compte dans un même écran, avec bascule entre les deux.
class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _formKey = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();

  bool _registering = false;
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    final session = context.read<Session>();
    try {
      if (_registering) {
        await session.register(_name.text.trim(), _email.text.trim(), _password.text);
      } else {
        await session.login(_email.text.trim(), _password.text);
      }
    } on ApiException catch (failure) {
      if (!mounted) return;
      setState(() {
        _error = failure.message;
        _loading = false;
      });
    }
  }

  void _toggle() {
    setState(() {
      _registering = !_registering;
      _error = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 380),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const _Brand(),
                    const SizedBox(height: 40),
                    Text(_registering ? 'Créer un compte' : 'Connexion', style: AppText.title),
                    const SizedBox(height: 4),
                    Text(
                      _registering
                          ? 'Une minute suffit pour commencer à suivre vos dépenses.'
                          : 'Retrouvez vos dépenses et vos budgets.',
                      style: AppText.body.copyWith(color: AppColors.muted),
                    ),
                    const SizedBox(height: 24),
                    if (_error != null) ...[Notice(text: _error!), const SizedBox(height: 16)],
                    if (_registering) ...[
                      TextFormField(
                        controller: _name,
                        textInputAction: TextInputAction.next,
                        textCapitalization: TextCapitalization.words,
                        autofillHints: const [AutofillHints.name],
                        decoration: fieldDecoration('Nom complet'),
                        validator: (value) =>
                            (value ?? '').trim().length < 2 ? 'Indiquez votre nom.' : null,
                      ),
                      const SizedBox(height: 16),
                    ],
                    TextFormField(
                      controller: _email,
                      keyboardType: TextInputType.emailAddress,
                      textInputAction: TextInputAction.next,
                      autocorrect: false,
                      autofillHints: const [AutofillHints.email],
                      decoration: fieldDecoration('Adresse e-mail'),
                      validator: (value) =>
                          (value ?? '').contains('@') ? null : 'Indiquez une adresse e-mail valide.',
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _password,
                      obscureText: true,
                      textInputAction: TextInputAction.done,
                      onFieldSubmitted: (_) => _submit(),
                      decoration: fieldDecoration(
                        'Mot de passe',
                        helper: _registering ? '$_minPassword caractères au minimum.' : null,
                      ),
                      validator: (value) {
                        final length = (value ?? '').length;
                        if (length == 0) return 'Indiquez votre mot de passe.';
                        if (_registering && length < _minPassword) {
                          return 'Le mot de passe doit contenir au moins $_minPassword caractères.';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 24),
                    FilledButton(
                      style: primaryButtonStyle(),
                      onPressed: _loading ? null : _submit,
                      child: _loading
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                            )
                          : Text(_registering ? 'Créer mon compte' : 'Se connecter'),
                    ),
                    const SizedBox(height: 16),
                    TextButton(
                      onPressed: _loading ? null : _toggle,
                      child: Text(
                        _registering ? 'Déjà inscrit ? Se connecter' : 'Pas encore de compte ? Créer un compte',
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _Brand extends StatelessWidget {
  const _Brand();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(color: AppColors.primary, borderRadius: BorderRadius.circular(kRadius)),
          child: const Icon(Icons.account_balance_wallet_outlined, color: Colors.white, size: 20),
        ),
        const SizedBox(width: 12),
        const Text('Mes Dépenses', style: AppText.section),
      ],
    );
  }
}
