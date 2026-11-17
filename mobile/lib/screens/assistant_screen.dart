import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../api.dart';
import '../theme.dart';
import '../widgets.dart';

const _suggestions = [
  'Combien ai-je dépensé ce mois-ci ?',
  'Quelle est ma plus grosse dépense du mois ?',
  'Où en sont mes budgets ?',
  'Ajoute 2 000 FCFA de taxi',
  'Comment mieux tenir mon budget ?',
];

// Noms des outils renvoyés par l'API, traduits pour l'utilisateur.
const _toolLabels = {
  'total_depenses': 'total des dépenses',
  'depenses_par_categorie': 'répartition par catégorie',
  'lister_depenses': 'liste des dépenses',
  'etat_budgets': 'état des budgets',
  'ajouter_depense': "ajout d'une dépense",
};

class _ChatMessage {
  const _ChatMessage({required this.fromUser, required this.text, this.caption});

  final bool fromUser;
  final String text;
  final String? caption;
}

class AssistantScreen extends StatefulWidget {
  const AssistantScreen({super.key});

  @override
  State<AssistantScreen> createState() => _AssistantScreenState();
}

class _AssistantScreenState extends State<AssistantScreen> {
  final _input = TextEditingController();
  final _scroll = ScrollController();
  final List<_ChatMessage> _messages = [];
  int? _conversationId;
  bool _waiting = false;
  String? _error;

  @override
  void dispose() {
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    // Le défilement attend que la liste ait été reconstruite avec le nouveau message.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(
          _scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _send(String text) async {
    final message = text.trim();
    if (message.isEmpty || _waiting) return;
    setState(() {
      _messages.add(_ChatMessage(fromUser: true, text: message));
      _waiting = true;
      _error = null;
    });
    _input.clear();
    _scrollToBottom();

    final api = context.read<ApiClient>();
    try {
      final answer = await api.askAssistant(message, _conversationId);
      if (!mounted) return;
      String? caption;
      if (answer.toolsUsed.isNotEmpty) {
        final sources = answer.toolsUsed.map((tool) => _toolLabels[tool] ?? tool).join(', ');
        caption = '${answer.dataChanged ? 'Action : ' : 'Calculé à partir de : '}$sources';
      }
      setState(() {
        _conversationId = answer.conversationId;
        _messages.add(_ChatMessage(fromUser: false, text: answer.reply, caption: caption));
        _waiting = false;
      });
    } on ApiException catch (failure) {
      if (!mounted) return;
      // La question est remise dans le champ : l'utilisateur peut la renvoyer sans la retaper.
      setState(() {
        _messages.removeLast();
        _error = failure.message;
        _waiting = false;
      });
      _input.text = message;
    }
    _scrollToBottom();
  }

  void _reset() {
    setState(() {
      _messages.clear();
      _conversationId = null;
      _error = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    final empty = _messages.isEmpty && !_waiting;
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 24, 8, 8),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Expanded(
                child: ScreenHeader(title: 'Assistant', subtitle: 'Vos dépenses, ou toute autre question.'),
              ),
              if (!empty)
                IconButton(
                  tooltip: 'Nouvelle conversation',
                  icon: const Icon(Icons.add_comment_outlined, color: AppColors.muted),
                  onPressed: _waiting ? null : _reset,
                ),
            ],
          ),
        ),
        Expanded(
          child: empty
              ? _Welcome(onPick: _send)
              : ListView.builder(
                  controller: _scroll,
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                  itemCount: _messages.length + (_waiting ? 1 : 0),
                  itemBuilder: (context, index) {
                    if (index == _messages.length) {
                      return const _Bubble(
                        message: _ChatMessage(fromUser: false, text: "L'assistant rédige sa réponse..."),
                        pending: true,
                      );
                    }
                    return _Bubble(message: _messages[index]);
                  },
                ),
        ),
        if (_error != null)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
            child: Notice(text: _error!),
          ),
        Container(
          decoration: const BoxDecoration(
            color: AppColors.surface,
            border: Border(top: BorderSide(color: AppColors.border)),
          ),
          padding: const EdgeInsets.fromLTRB(16, 10, 8, 10),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _input,
                  maxLength: 1000,
                  minLines: 1,
                  maxLines: 4,
                  textCapitalization: TextCapitalization.sentences,
                  textInputAction: TextInputAction.send,
                  onSubmitted: _send,
                  decoration: fieldDecoration('Votre message', hint: 'Écrivez votre question')
                      .copyWith(counterText: ''),
                ),
              ),
              const SizedBox(width: 4),
              IconButton(
                tooltip: 'Envoyer',
                icon: const Icon(Icons.send_rounded),
                color: AppColors.primary,
                onPressed: _waiting ? null : () => _send(_input.text),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _Welcome extends StatelessWidget {
  const _Welcome({required this.onPick});

  final ValueChanged<String> onPick;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            Container(
              width: 48,
              height: 48,
              decoration: const BoxDecoration(color: AppColors.surface, shape: BoxShape.circle),
              child: const Icon(Icons.forum_outlined, color: AppColors.muted),
            ),
            const SizedBox(height: 16),
            const Text('Que voulez-vous savoir ?', style: AppText.section),
            const SizedBox(height: 8),
            Text(
              "Les chiffres viennent de vos dépenses et de vos budgets. Pour le reste, l'assistant répond à partir de ses connaissances générales, sans accès à internet.",
              style: AppText.body.copyWith(color: AppColors.muted),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 20),
            for (final suggestion in _suggestions)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: OutlinedButton(
                  style: secondaryButtonStyle(),
                  onPressed: () => onPick(suggestion),
                  child: Text(suggestion),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _Bubble extends StatelessWidget {
  const _Bubble({required this.message, this.pending = false});

  final _ChatMessage message;
  final bool pending;

  @override
  Widget build(BuildContext context) {
    final fromUser = message.fromUser;
    final caption = message.caption;
    const corner = Radius.circular(12);
    const tail = Radius.circular(4);
    return Align(
      alignment: fromUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 6),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.82),
        decoration: BoxDecoration(
          color: fromUser ? AppColors.primary : AppColors.surface,
          border: fromUser ? null : Border.all(color: AppColors.border),
          borderRadius: BorderRadius.only(
            topLeft: corner,
            topRight: corner,
            bottomLeft: fromUser ? corner : tail,
            bottomRight: fromUser ? tail : corner,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              message.text,
              style: AppText.body.copyWith(
                color: fromUser ? Colors.white : (pending ? AppColors.muted : AppColors.text),
              ),
            ),
            if (caption != null) ...[
              const SizedBox(height: 8),
              const Divider(height: 1, color: AppColors.border),
              const SizedBox(height: 8),
              Text(caption, style: AppText.small),
            ],
          ],
        ),
      ),
    );
  }
}
