int	max(int *tab, unsigned int len)
{
	unsigned int	cmp;
	int				cpy;

	if (len == 0)
		return (0);
	cmp = 0;
	cpy = tab[0];
	while (cmp < len)
	{
		if (cpy < tab[cmp])
			cpy = tab[cmp];
		++cmp;
	}
	return (cpy);
}
