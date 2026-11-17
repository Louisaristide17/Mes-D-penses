typedef Json = Map<String, dynamic>;

List<T> _list<T>(dynamic value, T Function(Json) build) {
  return (value as List<dynamic>).map((item) => build(item as Json)).toList();
}

class User {
  const User({required this.id, required this.name, required this.email});

  final int id;
  final String name;
  final String email;

  factory User.fromJson(Json json) {
    return User(id: json['id'] as int, name: json['name'] as String, email: json['email'] as String);
  }
}

// Nommée ExpenseCategory car Flutter exporte déjà une classe Category.
class ExpenseCategory {
  const ExpenseCategory({
    required this.id,
    required this.name,
    required this.color,
    required this.icon,
    required this.isDefault,
  });

  final int id;
  final String name;
  final String color;
  final String icon;
  final bool isDefault;

  factory ExpenseCategory.fromJson(Json json) {
    return ExpenseCategory(
      id: json['id'] as int,
      name: json['name'] as String,
      color: json['color'] as String,
      icon: json['icon'] as String,
      isDefault: json['is_default'] as bool,
    );
  }
}

class Expense {
  const Expense({
    required this.id,
    required this.amount,
    required this.date,
    required this.note,
    required this.category,
  });

  final int id;
  final int amount;
  final DateTime date;
  final String note;
  final ExpenseCategory category;

  factory Expense.fromJson(Json json) {
    return Expense(
      id: json['id'] as int,
      amount: json['amount'] as int,
      date: DateTime.parse(json['date'] as String),
      note: json['note'] as String,
      category: ExpenseCategory.fromJson(json['category'] as Json),
    );
  }
}

class ExpensePage {
  const ExpensePage({required this.items, required this.total});

  final List<Expense> items;
  final int total;

  factory ExpensePage.fromJson(Json json) {
    return ExpensePage(items: _list(json['items'], Expense.fromJson), total: json['total'] as int);
  }
}

class Suggestion {
  const Suggestion({required this.category, required this.confidence});

  final ExpenseCategory? category;
  final double confidence;

  factory Suggestion.fromJson(Json json) {
    final category = json['category'];
    return Suggestion(
      category: category == null ? null : ExpenseCategory.fromJson(category as Json),
      confidence: (json['confidence'] as num).toDouble(),
    );
  }
}

class BudgetStatus {
  const BudgetStatus({
    required this.budgetId,
    required this.category,
    required this.ceiling,
    required this.spent,
    required this.remaining,
    required this.ratio,
    required this.level,
  });

  final int budgetId;
  final ExpenseCategory category;
  final int ceiling;
  final int spent;
  final int remaining;
  final double ratio;

  /// "ok", "attention" ou "depasse".
  final String level;

  factory BudgetStatus.fromJson(Json json) {
    return BudgetStatus(
      budgetId: json['budget_id'] as int,
      category: ExpenseCategory.fromJson(json['category'] as Json),
      ceiling: json['ceiling'] as int,
      spent: json['spent'] as int,
      remaining: json['remaining'] as int,
      ratio: (json['ratio'] as num).toDouble(),
      level: json['level'] as String,
    );
  }
}

class CategoryTotal {
  const CategoryTotal({required this.category, required this.total, required this.share});

  final ExpenseCategory category;
  final int total;
  final double share;

  factory CategoryTotal.fromJson(Json json) {
    return CategoryTotal(
      category: ExpenseCategory.fromJson(json['category'] as Json),
      total: json['total'] as int,
      share: (json['share'] as num).toDouble(),
    );
  }
}

class MonthTotal {
  const MonthTotal({required this.month, required this.total});

  final String month;
  final int total;

  factory MonthTotal.fromJson(Json json) {
    return MonthTotal(month: json['month'] as String, total: json['total'] as int);
  }
}

class DashboardSummary {
  const DashboardSummary({
    required this.month,
    required this.total,
    required this.count,
    required this.variation,
    required this.byCategory,
    required this.monthly,
    required this.alerts,
    required this.recent,
  });

  final String month;
  final int total;
  final int count;

  /// Écart relatif avec le mois précédent, ou null s'il n'y avait aucune dépense.
  final double? variation;
  final List<CategoryTotal> byCategory;
  final List<MonthTotal> monthly;
  final List<BudgetStatus> alerts;
  final List<Expense> recent;

  factory DashboardSummary.fromJson(Json json) {
    final variation = json['variation'];
    return DashboardSummary(
      month: json['month'] as String,
      total: json['total'] as int,
      count: json['count'] as int,
      variation: variation == null ? null : (variation as num).toDouble(),
      byCategory: _list(json['by_category'], CategoryTotal.fromJson),
      monthly: _list(json['monthly'], MonthTotal.fromJson),
      alerts: _list(json['alerts'], BudgetStatus.fromJson),
      recent: _list(json['recent'], Expense.fromJson),
    );
  }
}

class AssistantAnswer {
  const AssistantAnswer({
    required this.conversationId,
    required this.reply,
    required this.toolsUsed,
    required this.dataChanged,
  });

  final int conversationId;
  final String reply;
  final List<String> toolsUsed;

  /// Vrai si l'assistant a enregistré une dépense.
  final bool dataChanged;

  factory AssistantAnswer.fromJson(Json json) {
    return AssistantAnswer(
      conversationId: json['conversation_id'] as int,
      reply: json['reply'] as String,
      toolsUsed: (json['tools_used'] as List<dynamic>).map((tool) => tool as String).toList(),
      dataChanged: json['data_changed'] as bool,
    );
  }
}
