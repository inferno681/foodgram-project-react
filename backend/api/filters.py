def recipe_filter(self, queryset, name, value):

    if name == 'author':
        return queryset.filter(author__username=value)

    if name == 'tags':
        tags = value.split(',')
        return queryset.filter(tags__slug__in=tags)

    if name == 'is_favorited':
        if value == '1':
            return queryset.filter(favorite__user=self.request.user)
        elif value == '0':
            return queryset.exclude(favorite__user=self.request.user)

    return queryset
