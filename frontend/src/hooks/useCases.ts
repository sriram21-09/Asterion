import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { caseService } from '@/services/case.service';
import type { CreateCaseDTO } from '@/types/case';
import { toast } from 'sonner';

const CACHE_KEY = ['cases'];

export const useCases = () => {
  return useQuery({
    queryKey: CACHE_KEY,
    queryFn: caseService.getCases,
  });
};

export const useCase = (id: number) => {
  return useQuery({
    queryKey: [...CACHE_KEY, id],
    queryFn: () => caseService.getCase(id),
    enabled: !!id,
  });
};

export const useCreateCase = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateCaseDTO) => caseService.createCase(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEY });
      toast.success('Case created successfully');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to create case');
    },
  });
};

export const useDeleteCase = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => caseService.deleteCase(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CACHE_KEY });
      toast.success('Case deleted successfully');
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to delete case');
    },
  });
};
