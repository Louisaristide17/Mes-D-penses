import 'package:flutter/material.dart';

import '../theme.dart';
import 'assistant_screen.dart';
import 'budgets_screen.dart';
import 'dashboard_screen.dart';
import 'expense_form.dart';
import 'expenses_screen.dart';
import 'profile_screen.dart';

/// Structure de l'application connectée : cinq onglets et le bouton d'ajout.
class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _tab = 0;

  // Incrémenté après chaque ajout : les écrans sont recréés et rechargent leurs données.
  int _version = 0;

  Future<void> _addExpense() async {
    final saved = await showExpenseForm(context);
    if (saved && mounted) setState(() => _version++);
  }

  @override
  Widget build(BuildContext context) {
    final Widget page;
    switch (_tab) {
      case 0:
        page = DashboardScreen(key: ValueKey('dashboard-$_version'), onSeeAll: () => setState(() => _tab = 1));
      case 1:
        page = ExpensesScreen(key: ValueKey('expenses-$_version'));
      case 2:
        page = BudgetsScreen(key: ValueKey('budgets-$_version'));
      case 3:
        page = const AssistantScreen();
      default:
        page = const ProfileScreen();
    }

    return Scaffold(
      body: SafeArea(bottom: false, child: page),
      floatingActionButton: _tab <= 1
          ? FloatingActionButton.extended(
              onPressed: _addExpense,
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              icon: const Icon(Icons.add),
              label: const Text('Nouvelle dépense'),
            )
          : null,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (index) => setState(() => _tab = index),
        backgroundColor: AppColors.surface,
        indicatorColor: AppColors.primarySoft,
        surfaceTintColor: Colors.transparent,
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard, color: AppColors.primary),
            label: 'Accueil',
          ),
          NavigationDestination(
            icon: Icon(Icons.receipt_long_outlined),
            selectedIcon: Icon(Icons.receipt_long, color: AppColors.primary),
            label: 'Dépenses',
          ),
          NavigationDestination(
            icon: Icon(Icons.track_changes_outlined),
            selectedIcon: Icon(Icons.track_changes, color: AppColors.primary),
            label: 'Budgets',
          ),
          NavigationDestination(
            icon: Icon(Icons.forum_outlined),
            selectedIcon: Icon(Icons.forum, color: AppColors.primary),
            label: 'Assistant',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person, color: AppColors.primary),
            label: 'Profil',
          ),
        ],
      ),
    );
  }
}
